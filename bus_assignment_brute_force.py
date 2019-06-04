import ds_constants
from ds_route import ds_route
from ds_locations import ds_Student, ds_School, ds_Stop
from time import process_time

global start_time

#Fallback for when assingment to a route takes too long.
#Just try adding stops to a route in order until there's not
#enough space for the biggest bus to take it. Then assign the
#smallest bus that can take those stops. Repeat until all stops
#are taken.
def greedy_assignment(route, buses):
    routes = []
    picked_up = [False for stop in route.stops]
    while False in picked_up:
        bus = None
        for i in range(len(buses)):
            bus = buses[-1 - i]
            if bus[1] > 0:
                break
        capacity = bus[0]
        route_creating = ds_route()
        for i in range(len(route.stops)):
            if not picked_up[i]:
                route_creating.add_stop(route.stops[i])
                picked_up[i] = True
                if (not route_creating.is_acceptable(capacity) and
                    len(route_creating.stops) > 1):
                    route_creating.remove_stop(route.stops[i])
                    picked_up[i] = False
        for bus in buses:
            if bus[1] > 0 and route_creating.is_acceptable(bus[0]):
                route_creating.set_capacity(bus[0])
                bus[1] -= 1
                break
        if route_creating.unmodified_bus_capacity != None:
            routes.append(route_creating)
            print("onto next")
            continue
        #If no bus was large enough, should be for one stop.
        assert (len(route_creating.stops) == 1)
        to_use_bus = 0
        for bus in buses:
            if bus[1] > 0:
                to_use_bus = bus
        route_creating.set_capacity(to_use_bus[0])
        to_use_bus[1] -= 1
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
    if process_time() > start_time + ds_constants.BUS_SEARCH_TIME:
        return (False, None, 1e10)
    #If we're out of buses, return infeasibility
    if route_ind == len(buses_using) and False in picked_up:
        return (False, None, 1e10)
    #If the bus has too many students and multiple stops, return infeasibility
    if (not partial_routes[route_ind].is_acceptable(buses_using[route_ind]) and
        len(partial_routes[route_ind].stops) > 1):
        return (False, None, 1e10)
    #This one may cause issues with single-stop full-bus routes:
    #If the remaining buses do not have enough capacity, return infeasibility
    #if (sum([picked_up[i]*(1-route.stops[i].occs) for i in range(len(picked_up))]) >
    #    sum(buses_using[route_ind:]) - partial_routes[route_ind].occupants):
    #    return (False, None, 1e10)
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
            new_route = ds_route()
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
        if(route_ind == 0 and min_stop_ind == 1):
            print(stop_ind)
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
def try_hold(route, num_buses, buses):
    #First generate buses_using, a list of the n largest buses
    orig_num_buses = num_buses
    buses_using = []
    ind = -1
    while num_buses > 0:
        if buses[ind][1] >= num_buses:
            for i in range(num_buses):
                buses_using.append(buses[ind][0])
            break
        for i in range(buses[ind][1]):
            buses_using.append(buses[ind][0])
        num_buses -= buses[ind][1]
        ind -= 1
    #First, check whether it's even close to possible -
    #should save some time.
    #May cause errors wrt high-occupancy single stops, though
    #if sum(buses_using) < route.occupants:
    #    return (False, None, None)
    #Now check the possibilities
    out = check_possibilities(route, buses_using,
                              [ds_route() for i in range(orig_num_buses)],
                              [False for i in range(len(route.stops))],
                              0, 0, [])
    if out[0]:
        return (out[0], out[1], buses_using)
    return (False, None, None)
        
        
def assign_buses(routes, buses):
    global start_time
    routes = list(routes)
    routes.sort(key = lambda x:x.occupants)
    new_routes = []
    for route_ind, route in enumerate(routes):
                
        print(str(route_ind) + "/" + str(len(routes)))
        print("Used " + str(len(new_routes)) + " buses.")
        print("Assigning a route with " + str(len(route.stops)) + " stops.")
        num_buses = 0
        out = None
        start_time = process_time()
        while True:
            num_buses += 1
            if num_buses > 1:
                print("Trying " + str(num_buses) + " buses.")
            out = try_hold(route, num_buses, buses)
            if out[0]:
                break
            if process_time() - start_time > ds_constants.BUS_SEARCH_TIME:
                #Indicate that no solution was found by search
                print("****************Punting*******************")
                out = None
                break
            
        if out == None:
            greedy_routes = greedy_assignment(route, buses)
            for subroute in greedy_routes:
                new_routes.append(subroute)
            continue
        for subroute in out[1]:
            #If no bus is big enough to take the stop, just use the
            #biggest remaining one.
            #So first figure out what that is.
            biggest_bus = None
            for bus in buses:
                if bus[1] > 0:
                    biggest_bus = bus
            for bus in buses:
                #Acceptable either if the capacity is satisifed OR we
                #take the largest remaining bus and only pick up one stop
                if bus[1] > 0 and (subroute.is_acceptable(bus[0]) or
                                  len(subroute.stops) == 1 and bus == biggest_bus):
                    subroute.unmodified_bus_capacity = bus[0]
                    bus[1] -= 1
                    new_routes.append(subroute)
                    print(str(bus[0]) + " " + str(subroute.occupants) + " " + str(len(subroute.stops)))
                    break
    return new_routes

from ds_setup import setup_buses
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_buses(prefix+'dist_bus_capacities.csv')
final_routes = assign_buses(improved_apple, buses)
