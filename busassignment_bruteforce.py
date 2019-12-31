import constants
from diagnostics import printout
from route import Route
from locations import Student, School, Stop
from time import process_time

global start_time

#Fallback for when assignment to a route takes too long.
#Just try adding stops to a route in order until there's not
#enough space for the biggest bus to take it. Then assign the
#smallest bus that can take those stops. Repeat until all stops
#are taken.
def greedy_assignment(route, buses):
    routes = []
    picked_up = [False for stop in route.stops]
    while False in picked_up:
        bus = None
        for bus in buses[::-1]:
            #Found an unassigned bus
            if bus.route == None:
                break
        if bus == None:
            print("Out of buses. Terminating bus assignment.")
            break
        route_creating = Route()
        for i in range(len(route.stops)):
            if not picked_up[i]:
                route_creating.add_stop(route.stops[i])
                picked_up[i] = True
                if (not bus.can_handle(route_creating)):
                    route_creating.remove_stop(route.stops[i])
                    picked_up[i] = False
        for bus in buses:
            if bus.can_handle(route_creating):
                bus.assign(route_creating)
                break
        if route_creating.bus != None:
            routes.append(route_creating)
            continue
        #If no bus was large enough, should be for one stop.
        assert (len(route_creating.stops) == 1), str(len(route_creating.stops))
        for bus in buses[::-1]:
            if bus.route == None:
                break
        bus.assign(route_creating)
        routes.append(route_creating)
    return routes

#Recursive function to assist with checking all possibilities
#for assignment of stops to buses.
#route is the parent route, buses_using is the list of bus
#capacities, picked_up is a tuple of booleans denoting which stops
#on the route have been selected, partial_routes is a tuple of
#the routes which are in the process of being generated
#route_ind is the index of the route which is currently being
#worked on, and stop_ind is the smallest index of stops which
#should still be considered for this route.
#starts is a list of tuples (capacity, first stop index) to avoid
#repeating duplicate work by swapping two buses of the same capacity
def check_possibilities(route, buses_using, partial_routes, picked_up,
                        route_ind, min_stop_ind, starts):
    global start_time
    if process_time() > start_time + constants.BUS_SEARCH_TIME:
        return (False, None, 1e10)
    #If we're out of buses, return infeasibility
    if route_ind == len(buses_using) and False in picked_up:
        return (False, None, 1e10)
    #If the bus has too many students and multiple stops, return infeasibility
    if (not buses_using[route_ind].can_handle(partial_routes[route_ind]) and
        len(partial_routes[route_ind].stops) > 1):
        return (False, None, 1e10)
    #If the last bus has passed a stop that needs to be picked up, return infeasibility
    if route_ind == len(buses_using) - 1 and False in picked_up[:min_stop_ind]:
        return (False, None, 1e10)
    #If only one capacity remains and a bus with such capacity has passed
    #a stop that needs to be picked up before starting the route, return
    #infeasibility to avoid duplicating work.
    if (buses_using[route_ind] == buses_using[-1] and
        len(partial_routes[route_ind].stops) == 0 and
        False in picked_up[:min_stop_ind]):
        return (False, None, 1e10)
    #If all stops have been picked up, this is a feasible solution.
    if False not in picked_up:
        trav_times = []
        #Determine the total travel time
        for route in partial_routes:
            trav_times.extend(route.student_travel_times())
        total_trav_time = sum(trav_times)
        completed_routes = []
        for route in partial_routes:
            new_route = Route()
            for stop in route.stops:
                new_route.add_stop(stop)
            completed_routes.append(new_route)
        return (True, completed_routes, total_trav_time)
    best = (False, None, 1e10)
    #First, check completion of the current route.
    out = check_possibilities(route, buses_using, partial_routes, picked_up,
                              route_ind + 1, 0, starts)
    if out[2] < best[2]:
        best = out
    for stop_ind in range(min_stop_ind, len(picked_up)):
        if not picked_up[stop_ind]:
            #Case where we would be duplicating work
            #We're starting a route at an earlier time than
            #another bus with the same capacity.
            if len(partial_routes[route_ind].stops) == 0:
                duplicating = False
                for start in starts:
                    if start[0] == buses_using[route_ind] and stop_ind < start[1]:
                        duplicating = True
                if duplicating:
                    continue
            partial_routes[route_ind].add_stop(route.stops[stop_ind])
            picked_up[stop_ind] = True
            if len(partial_routes[route_ind].stops) == 1:
                starts.append((buses_using[route_ind], stop_ind))
            out = check_possibilities(route, buses_using, partial_routes, picked_up,
                                      route_ind, stop_ind + 1, starts)
            if len(partial_routes[route_ind].stops) == 1:
                del starts[-1]
            picked_up[stop_ind] = False
            if out[2] < best[2]:
                best = out
            partial_routes[route_ind].remove_stop(route.stops[stop_ind])
            #Another case where we would be duplicating work
            #If all remaining buses have the same capacity, we may
            #as well start at the first untaken stop. So break after
            #trying the first untaken stop.
            if (buses_using[route_ind] == buses_using[-1] and
                len(partial_routes[route_ind].stops) == 0):
                break
    return best

#Check whether it's possible for the num_buses largest buses
#to take all of the stops.
#Returns a tuple where the first entry is whether it's possible
#and the second and third entries are None if it's impossible and
#the list of routes and the list of buses used if it's possible.
def try_hold(route, num_buses, buses, picked_up):
    #First generate buses_using, a list of the n largest buses
    orig_num_buses = num_buses
    buses_using = buses[len(buses)-num_buses:]
    out = check_possibilities(route, buses_using,
                              [Route() for i in range(orig_num_buses)],
                              picked_up,
                              0, 0, [])
    if out[0]:
        return (out[0], out[1], buses_using)
    return (False, None, None)
        
     
#Assigns wheelchair students to buses, and when possible adds
#as many non-wheelchair students as it can.
#routes_so_far
def assign_lift(route, buses, picked_up):
    new_route = Route()
    for stop_ind, stop in enumerate(route.stops):
        if picked_up[stop_ind]:
            continue
        #If this is a wheelchair stop, see whether we can add it to the route
        if stop.count_needs("W") > 0 or stop.count_needs("L") > 0:
            new_route.add_stop(stop)
            picked_up[stop_ind] = True
            possible = False
            for bus in buses:
                if bus.route == None and bus.lift and bus.can_handle(new_route):
                    possible = True
                    break
            if not possible:
                new_route.remove_stop(stop)
                picked_up[stop_ind] = False
    #Now as many wheelchair students as can fit on one
    #bus have been picked up. Add other students if possible
    for stop_ind, stop in enumerate(route.stops):
        if picked_up[stop_ind]:
            continue
        if stop.count_needs("W") == 0 and stop.count_needs("L") == 0:
            if not new_route.add_stop(stop):
                continue
            picked_up[stop_ind] = True
            possible = False
            for bus in buses:
                if bus.route == None and bus.lift and bus.can_handle(new_route):
                    possible = True
                    break
            if not possible:
                new_route.remove_stop(stop)
                picked_up[stop_ind] = False
    for bus in buses:
        if bus.lift and bus.can_handle(new_route):
            assert bus.assign(new_route)
            break
    #Keep stops in the same order. This ensures that the travel time
    #doesn't increase, violating regulations.
    new_route.stops.sort(key = lambda s: route.stops.index(s))
    new_route.recompute_length()
    buses.remove(new_route.bus)
    #If we failed to pick up all wheelchair students,
    #need to continue assigning wheelchair buses.
    recursive_routes = []
    for stop_ind, stop in enumerate(route.stops):
        if (not picked_up[stop_ind] and
            (stop.count_needs("W") > 0 or stop.count_needs("L") > 0)):
            recursive_routes = assign_lift(route, buses, picked_up)
    recursive_routes.append(new_route)
    assert new_route.feasibility_check(verbose = True)
    return recursive_routes
   

def assign_buses(routes, buses):
    global start_time
    buses.sort(key = lambda x: x.capacity)
    routes = list(routes)
    routes.sort(key = lambda x:x.occupants)
    new_routes = []
    for route_ind, route in enumerate(routes):
        #Reporting
        if len(buses) == 0:
            new_routes.append(route)
            continue
        
        picked_up = [False for i in range(len(route.stops))]
        #Before entering the recursive procedure, assign buses for
        #wheelchair students if any exist.
        for stud in route.special_ed_students:
            if stud.has_need("W") or stud.has_need("L"):
                l_routes = assign_lift(route, buses, picked_up)
                new_routes.extend(l_routes)
                break
        #It's possible that the wheelchair buses were
        #able to pick up all of the students.
        if False not in picked_up:
            continue
        
        #Due to checks in the brute force bus assignment
        #procedure that rely on a certain order of processing
        #for possible permutations, it's necessary to pass
        #in a route none of whose stops have been picked up.
        #Therefore, create a virtual route with all of the
        #unvisited stops.
        virtual_route = Route()
        for (stop_ind, stop) in enumerate(route.stops):
            if not picked_up[stop_ind]:
                virtual_route.add_stop(stop)
        picked_up = [False for i in range(len(virtual_route.stops))]
        num_buses = 0
        out = None
        start_time = process_time()
        while False in picked_up:
            num_buses += 1
            out = try_hold(virtual_route, num_buses, buses, picked_up)
            if out[0]:
                break
            if process_time() - start_time > constants.BUS_SEARCH_TIME:
                #No solution was found by search. Punt
                out = None
                break
        if out == None:
            greedy_routes = greedy_assignment(virtual_route, buses)
            for subroute in greedy_routes:
                new_routes.append(subroute)
            continue
        for subroute in out[1]:
            #If no bus is big enough to take the stop, just use the
            #biggest remaining one.
            #So first figure out what that is.
            biggest_bus = None
            for bus in buses[::-1]:
                if bus.route == None:
                    biggest_bus = bus
            for bus in buses:
                #Acceptable either if the capacity is satisifed OR we
                #take the largest remaining bus and only pick up one stop
                if (bus.can_handle(subroute) or
                    len(subroute.stops) == 1 and bus == biggest_bus):
                    subroute.bus = bus
                    bus.route = subroute
                    subroute.bus = bus
                    new_routes.append(subroute)
                    break
            buses.remove(subroute.bus)
    return new_routes