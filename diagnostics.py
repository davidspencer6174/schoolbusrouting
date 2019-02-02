from locations import School, Student
import pickle

geocodes = open("data//all_geocodes.csv", "r")
codes = []
for code in geocodes.readlines():
    codes.append(code.strip())

def printout(locs, full = False):
    printout_google_maps(locs)
    #print out route
    if not full:
        return
    for loc in locs:
        if isinstance(loc, School):
            print("School at tt index " + str(loc.tt_ind))
        else:
            print("Student at tt index " + str(loc.tt_ind))
    
    #print where each student goes to school
    for i in locs:
        if isinstance(i, Student):
            print("tt ind " + str(i.tt_ind) + " to school " + str(i.school.tt_ind))

#Takes an index in the travel time matrix and returns the link with the
#latitude-longitude pair appended            
def append_to_link(link, tt_ind):
    latlong = codes[tt_ind].split(";")
    link += "/"
    link += latlong[0]
    link += ","
    link += latlong[1]
    return link
            
def printout_google_maps(locs):
    link = "https://www.google.com/maps/dir"
    appended = 0
    for i in range(len(locs)):
        if i == 0 or locs[i].tt_ind != locs[i-1].tt_ind:
            link = append_to_link(link, locs[i].tt_ind)
            appended += 1
            #Can only have 10 locations in a Maps link, so need to do another
            #link
            if appended == 10:
                print(link)
                print("Need to start an additional link")
                link = "https://www.google.com/maps/dir"
                link = append_to_link(link, locs[i].tt_ind)
    print(link)

def diagnostics(route_iter):
    #visits most schools
    most_schools = 0
    most_schools_route = None
    for j in range(len(route_iter)):
        cur_schools = 0
        locs = route_iter[j].locations
        for i in range(1, len(locs)):
            if isinstance(locs[i], School):
                if locs[i].tt_ind != locs[i-1].tt_ind:
                    cur_schools += 1
        if cur_schools > most_schools:
            most_schools = cur_schools
            most_schools_route = route_iter[j]
    print("Most schools: " + str(most_schools))
    print("Length: " + str(most_schools_route.length))
    printout(most_schools_route.locations)
    
    #visits most distinct locations
    most_locs = 0
    most_locs_route = None
    for j in range(len(route_iter)):
        cur_locs = 1
        locs = route_iter[j].locations
        for i in range(1, len(locs)):
            if locs[i].tt_ind != locs[i-1].tt_ind:
                cur_locs += 1
        if cur_locs > most_locs:
            most_locs = cur_locs
            most_locs_route = route_iter[j]
    print("********************************************************")
    print("Most distinct locations: " + str(most_locs))
    print("Length: " + str(most_locs_route.length))
    printout(most_locs_route.locations)
    
    #most riders while having mixed loads
    most_occs = 0
    for j in range(len(route_iter)):
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
            most_occs_route = route_iter[j]
    print("********************************************************")
    print("Most occupants with mixed loads: " + str(most_occs))
    print("Length: " + str(most_occs_route.length))
    printout(most_occs_route.locations)
    
loading = open("output//testing_refactor0.obj", "rb")
obj = pickle.load(loading)
diagnostics(obj)
loading.close()