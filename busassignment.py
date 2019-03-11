import constants
from route import Route
from locations import Student, School

#routes is any iterable of the routes we want to assign
#buses is a list of lists of length 2 [capacity, count]
#the buses will be modified to whichever buses remain
#after the assignment
#the routes list will be sorted
#TODO: Implement use of contract buses

def assign_buses(routes, buses):
    routes = sorted(routes, key = lambda r:r.occupants)
    buses = sorted(buses, key = lambda b:b[0])
    cap_map = constants.CAPACITY_MODIFIED_MAP
    resulting_routes = list()
    
    consumed = 0
    for r in routes:
        occs = r.occupants
        print("Bus assignment for route of occs " + str(occs))
        #Only handles elementary, middle, high
        type_ind = constants.TYPE_IND_MAP[r.locations[0].type]
        #Keep assigning buses until there are no students left.
        #Use the smallest possible bus
        while occs > 0:
            bus_used = None
            adding_route = None
            for b in buses:
                if cap_map[b[0]][type_ind] >= occs:
                    #get rid of unvisited schools
                    student_schools = set()
                    visited_schools = set()
                    for loc in r.locations:
                        if isinstance(loc, Student):
                            student_schools.add(loc.school)
                        else:
                            visited_schools.add(loc)
                    for school in visited_schools:
                        if school not in student_schools:
                            r.locations.remove(school)
                    r.recompute_length()
                    r.recompute_maxtime()
                    r.recompute_occs()
                    occs = 0
                    b[1] -= 1
                    bus_used = b
                    consumed += 1
                    resulting_routes.append(r)
                    adding_route = r
                    r.set_capacity(b[0])
                    if not r.feasibility_check():
                        print("Bad - final")
                    break
            #Nothing large enough for all - take as many as possible
            if bus_used == None:
                bus_used = buses[-1]
                bus_used[1] -= 1
                consumed += 1
                #create the route that this bus will take,
                #removing the corresponding students from
                #the existing route
                new_route = Route()
                #to set the bus capacity, the route needs to know its student
                #size.
                #TODO: find a cleaner way to do this, this is a bad hack
                for loc in r.locations:
                    if isinstance(loc, Student):
                        new_route.locations = [loc]
                        break
                new_route.set_capacity(bus_used[0])
                new_route.locations = []
                still_to_add = new_route.bus_capacity
                schools_to_visit = set()
                #pull students from the existing route and
                #their schools
                for loc in r.locations:
                    if isinstance(loc, Student) and still_to_add > 0:
                        still_to_add -= 1
                        new_route.add_location(loc)
                        schools_to_visit.add(loc.school)
                    if isinstance(loc, School) and loc in schools_to_visit:
                        new_route.add_location(loc)
                #check feasibility
                new_route.recompute_length()
                new_route.recompute_occs()
                new_route.recompute_maxtime()
                if not new_route.feasibility_check(verbose = True):
                    print("Bad - splitting")
                    print(new_route.length)
                    print(new_route.max_time)
                    print(r.length)
                    print(r.max_time)
                    if new_route.length > r.length:
                        print(new_route.locations)
                        print(r.locations)
                #remove from existing route
                for loc in new_route.locations:
                    if isinstance(loc, Student):
                        r.locations.remove(loc)
                        occs -= 1
                resulting_routes.append(new_route)
                adding_route = new_route
            #if we've used the last bus, get it out of the list
            print(str(bus_used[0]) + " " + str(adding_route.bus_capacity))
            if bus_used[1] == 0:
                buses.remove(bus_used)
    return (consumed, resulting_routes)
        