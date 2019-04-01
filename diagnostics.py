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
    locs = route.locations
    print("Estimated time: " + str(route.length/60) + " minutes.")
    if locs[0].type == "H":
        print("Picking up high school students")
    if locs[0].type == "M":
        print("Picking up middle school students")
    if locs[0].type == "E":
        print("Picking up elementary school students")
    print("Bus capacity: " + str(route.unmodified_bus_capacity))
    print("Bus capacity adjusted for student size: " + str(route.bus_capacity))
    total_students = 0
    for i in locs:
        if isinstance(i, Student):
            total_students += 1
    print("Number of assigned students: " + str(total_students))
    
    tt_ind_current = -1
    dropoffs = dict()
    students_picked_up = dict()
    #print out route
    for loc in locs:
        if loc.tt_ind != tt_ind_current:
            if tt_ind_current in dropoffs:
                for school in dropoffs[tt_ind_current]:
                    print("Drop off student(s) who go to " + school)
            tt_ind_current = loc.tt_ind
            if len(students_picked_up) > 0:
                for cost_cent in students_picked_up:
                    if students_picked_up[cost_cent] > 1:
                        print("Pick up " + str(students_picked_up[cost_cent]) +
                              " students who go to " + str(cost_cent))
                    else:
                        print("Pick up 1 student who goes to " + str(cost_cent))
            print(append_to_link("Go to latitude-longitude ", tt_ind_current, slash=False))
            schools_visited = set()
            students_picked_up = dict()
        if isinstance(loc, Student):
            if loc.fields[2] in students_picked_up:
                students_picked_up[loc.fields[2]] += 1
            else:
                students_picked_up[loc.fields[2]] = 1
            if loc.school.tt_ind not in dropoffs:
                dropoffs[loc.school.tt_ind] = set()
            dropoffs[loc.school.tt_ind].add(loc.fields[2])
        else:
            schools_visited.add(loc)
    if tt_ind_current in dropoffs:
        for school in dropoffs[tt_ind_current]:
            print("Drop off student(s) who go to " + school)
    if len(students_picked_up) > 0:
        for cost_cent in students_picked_up:
            if students_picked_up[cost_cent] > 1:
                print("Pick up " + str(students_picked_up[cost_cent]) +
                              " students who go to " + str(cost_cent))
            else:
                print("Pick up 1 student who goes to " + str(cost_cent))
    print("Google maps link: ")        
    printout_google_maps(route)
    print("Ending printout of route.")
    print("*********************************************************")
    print("*********************************************************")
    for i in range(3):
        print()
            
def printout_google_maps(route):
    locs = route.locations
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
        schools = 0
        students = 0
        for loc in route.locations:
            if isinstance(loc, School):
                schools += 1
            if isinstance(loc, Student):
                students += 1
        if schools > 1:
            num_mixedload += 1
        else:
            num_singleload += 1
        num_students += students
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
    for j in range(len(route_list)):
        cur_schools = 0
        locs = route_list[j].locations
        for i in range(1, len(locs)):
            if isinstance(locs[i], School):
                if locs[i].tt_ind != locs[i-1].tt_ind:
                    cur_schools += 1
        if cur_schools > most_schools:
            most_schools = cur_schools
            most_schools_route = route_list[j]
    print("Most schools on one route: " + str(most_schools))
    printout(most_schools_route)
    
    #visits most distinct locations
    most_locs = 0
    most_locs_route = None
    for j in range(len(route_list)):
        cur_locs = 1
        locs = route_list[j].locations
        for i in range(1, len(locs)):
            if locs[i].tt_ind != locs[i-1].tt_ind:
                cur_locs += 1
        if cur_locs > most_locs:
            most_locs = cur_locs
            most_locs_route = route_list[j]
    print("Most distinct locations on one route: " + str(most_locs))
    printout(most_locs_route)
    
    #most riders while having mixed loads
    most_occs = 0
    for j in range(len(route_list)):
        cur_occs = 0
        cur_schools = 0
        locs = route_iter[j].locations
        for i in range(0, len(locs)):
            if isinstance(locs[i], Student):
                cur_occs += 1
            if isinstance(locs[i], School):
                cur_schools += 1
        if cur_occs >= most_occs and cur_schools > 1:
            most_occs = cur_occs
            most_occs_route = route_list[j]
    print("Most occupants on a mixed-loads route: " + str(most_occs))
    printout(most_occs_route)
    
    #do all Taft routes
    for r in route_list:
        to_print = False
        for loc in r.locations:
            if isinstance(loc, Student):
                if (loc.fields[2].strip() == "TAFT CHS" or
                    loc.fields[2].strip() == "TAFT GIFTED STEAM MAG"):
                    to_print = True
        if to_print:
            print("Route that goes to Taft")
            printout(r)
    
loading = open("output//weightedcost602bused.obj", "rb")
#loading = open("output//greedymlmove60bused.obj", "rb")
obj = pickle.load(loading)
diagnostics(obj)
#print_all(obj)
loading.close()
            
