from locations import School, Student
import pickle

geocodes = open("data//all_geocodes.csv", "r")
codes = []
for code in geocodes.readlines():
    codes.append(code.strip())

#Takes an index in the travel time matrix and returns the link with the
#latitude-longitude pair appended            
def append_to_link(link, tt_ind, slash=True):
    latlong = codes[tt_ind].split(";")
    if slash:
        link += "/"
    link += latlong[0]
    link += ","
    link += latlong[1]
    return link

def printout(route):
    stops = route.stops
    schools = route.schools
    print("Estimated time: " + str(route.length/60) + " minutes.")
    if stops[0].type == "H":
        print("Picking up high school students")
    if stops[0].type == "M":
        print("Picking up middle school students")
    if stops[0].type == "E":
        print("Picking up elementary school students")
    print("Bus capacity: " + str(route.unmodified_bus_capacity))
    print("Bus capacity adjusted for student size: " + str(route.bus_capacity))
    print("Number of assigned students: " + str(route.occupants))
    
    for i in range(len(stops)):
        if i == 0 or (i > 0 and stops[i].tt_ind != stops[i - 1].tt_ind):
            print(append_to_link("Go to latitude-longitude ", stops[i].tt_ind,
                                 slash=False))
        if stops[i].occs > 1:
            print("Pick up " + str(stops[i].occs) +
                  " students who go to " + stops[i].school.school_name)
        else:
            print("Pick up " + str(stops[i].occs) +
                  " student who goes to " + stops[i].school.school_name)
    for i in range(len(schools)):
        if i == 0 or (i > 0 and schools[i].tt_ind != schools[i - 1].tt_ind):
            print(append_to_link("Go to latitude-longitude ", schools[i].tt_ind,
                                 slash=False))
        print("Drop off at " + schools[i].school_name)
            
    print("Google maps link: ")        
    printout_google_maps(route)
    print("Ending printout of route.")
    print("*********************************************************")
    print("*********************************************************")
    for i in range(3):
        print()
            
def printout_google_maps(route):
    locs = route.stops + route.schools
    link = "https://www.google.com/maps/dir"
    appended = 0
    for i in range(len(locs)):
        if i == 0 or locs[i].tt_ind != locs[i-1].tt_ind:
            link = append_to_link(link, locs[i].tt_ind)
            appended += 1
            #Can only have 10 locations in a Maps link, so need to do another
            #link
            if appended == 10 and i < len(locs) - 1:
                print(link)
                print("Need to start an additional link")
                link = "https://www.google.com/maps/dir"
                link = append_to_link(link, locs[i].tt_ind)
    print(link)
    
def print_all(route_iter):
    for r in route_iter:
        printout(r)

def diagnostics(route_iter):
    route_list = []
    total_time = 0
    num_students = 0
    num_mixedload = 0
    num_singleload = 0
    buses_used = dict()
    for route in route_iter:
        route_list.append(route)
        total_time += route.length
        if len(route.schools) > 1:
            num_mixedload += 1
        else:
            num_singleload += 1
        num_students += route.occupants
        if route.unmodified_bus_capacity in buses_used:
            buses_used[route.unmodified_bus_capacity] += 1
        else:
            buses_used[route.unmodified_bus_capacity] = 1
    print("Number of routes: " + str(len(route_list)))
    print("Number of students picked up: " + str(num_students))
    for cap in sorted(buses_used.keys()):
        print("Used " + str(buses_used[cap]) + " buses of capacity " + str(cap))
    print("Number of mixed-load routes: " + str(num_mixedload))
    print("Number of single-load routes: " + str(num_singleload))
    print("Average estimated time per route: " +
          str(total_time/len(route_list)/60) + " minutes.")
    print("Ending printout of summary statistics.")
    print("*********************************************************")
    print("*********************************************************")
    for i in range(3):
        print()
        
    
    #visits most schools
    most_schools = 0
    most_schools_route = None
    for route in route_list:
        cur_schools = len(route.schools)
        if cur_schools > most_schools:
            most_schools = cur_schools
            most_schools_route = route
    print("Most schools on one route: " + str(most_schools))
    printout(most_schools_route)
    
    #visits most distinct locations
    most_locs = 0
    most_locs_route = None
    for route in route_list:
        cur_locs = route.stops + route.schools
        num_locs = 0
        for i in range(len(cur_locs)):
            if i == 0 or (cur_locs[i].tt_ind != cur_locs[i - 1].tt_ind):
                num_locs += 1
        if num_locs > most_locs:
            most_locs = num_locs
            most_locs_route = route
    print("Most distinct locations on one route: " + str(most_locs))
    printout(most_locs_route)
    
    #most riders while having mixed loads
    most_occs = 0
    most_occs_route = None
    for route in route_list:
        cur_occs = route.occupants
        cur_schools = len(route.schools)
        if cur_occs >= most_occs and cur_schools > 1:
            most_occs = cur_occs
            most_occs_route = route
    print("Most occupants on a mixed-loads route: " + str(most_occs))
    printout(most_occs_route)
    
    #do all Taft routes
    for r in route_list:
        to_print = False
        for school in r.schools:
            if (school.school_name.strip() == "TAFT CHS" or
                school.school_name.strip() == "TAFT GIFTED STEAM MAG"):
                to_print = True
        if to_print:
            print("Route that goes to Taft")
            printout(r)
    
loading = open("output//fixedlastinsert55m.obj", "rb")
obj = pickle.load(loading)
diagnostics(obj)
#print_all(obj)
loading.close()
            
