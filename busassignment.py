import constants
from route import Route
from locations import Student, School, Stop

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
        if constants.VERBOSE:
            print("Bus assignment for route of occs " + str(occs))
        #Only handles elementary, middle, high
        type_ind = constants.TYPE_IND_MAP[r.stops[0].type]
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
                    for stop in r.stops:
                        student_schools.add(stop.school)
                    for school in r.schools:
                        visited_schools.add(school)
                    for school in visited_schools:
                        if school not in student_schools:
                            r.schools.remove(school)
                    r.recompute_length()
                    r.recompute_maxtime()
                    r.recompute_occupants()
                    occs = 0
                    b[1] -= 1
                    bus_used = b
                    consumed += 1
                    resulting_routes.append(r)
                    adding_route = r
                    r.set_capacity(b[0])
                    if not r.feasibility_check():
                        print("Bad")
                    break
            #Nothing large enough for all - take as many as possible
            if bus_used == None:
                new_route = Route()
                for stop in r.stops:
                    #Always assume that the first stop can be
                    #taken - in some cases, there are too many
                    #students at a stop to be feasibly picked up
                    #by a single bus.
                    if ((cap_map[buses[-1][0]][type_ind] >=
                        stop.occs + new_route.occupants) or
                        len(new_route.stops) == 0):
                        new_route.add_stop(stop)
                for b in buses:
                    #Need a clause to handle the case where too many
                    #students are at one stop.
                    if (cap_map[b[0]][type_ind] >= new_route.occupants or
                        b == buses[-1]):
                        occs -= new_route.occupants
                        b[1] -= 1
                        bus_used = b
                        consumed += 1
                        resulting_routes.append(new_route)
                        adding_route = new_route
                        new_route.set_capacity(b[0])
                        if not r.feasibility_check():
                            print("Bad")
                        break
                for stop in new_route.stops:
                    r.remove_stop(stop)
            if constants.VERBOSE:
                print(str(bus_used[0]) + " " + str(adding_route.bus_capacity))
            #if we've used the last bus, get it out of the list
            if bus_used[1] == 0:
                buses.remove(bus_used)
    return (consumed, resulting_routes)
        