import numpy as np
from locations import Stop, School
from route import Route
from utils import two_opt

#For the SBRP formulation of the Clarke-Wright savings
#procedure, we will follow the work "Modeling Mixed Load
#School Bus Routing" from Campbell, North, and Ellegood.

#Compute savings for adding route2 to the end of route1
def savings(route1, route2):
    if route1 == route2:
        return -1e10
    orig_cost = route1.length + route2.length
    route1.backup()
    route2.backup()
    for stop in route2.stops:
        if not route1.add_stop(stop):
            route1.restore()
            route2.restore()
            return -1e10
    two_opt(route1, report = False)
    new_cost = route1.length
    feasibility = route1.feasibility_check()
    route1.restore()
    route2.restore()
    assert route1.length + route2.length == orig_cost
    if not feasibility:
        return -1e10
    return (orig_cost - new_cost)

def update(stop1, stop2, stop_info_map, savings_matrix):
    route1 = stop_info_map[stop1][1]
    route2 = stop_info_map[stop2][1]
    i1 = stop_info_map[stop1][0]
    i2 = stop_info_map[stop2][0]
    savings_matrix[i1, i2] = savings(route1, route2)

def clarke_wright_savings(schools):
    routes = []
    #We wish to maintain a distance matrix for stops.
    #To do this, we'll need to index the stops and keep
    #track of which route each stop belongs to.
    #Use a dict to track these.
    stop_info_map = dict()
    ind_stop_map = dict()
    stop_ind_counter = 0
    schools = list(schools)
    schools.sort(key = lambda x: x.school_name)
    for school in schools:
        stops = list(school.unrouted_stops)
        stops.sort(key = lambda x: x.tt_ind)
        for stop in stops:
            new_route = Route()
            new_route.add_stop(stop)
            routes.append(new_route)
            stop_info_map[stop] = [stop_ind_counter, new_route]
            ind_stop_map[stop_ind_counter] = stop
            stop_ind_counter += 1
    savings_matrix = np.zeros((stop_ind_counter, stop_ind_counter))
    for i1 in range(stop_ind_counter):
        if i1 % 100 == 0:
            print(i1)
        for i2 in range(stop_ind_counter):
            update(ind_stop_map[i1], ind_stop_map[i2],
                   stop_info_map, savings_matrix)
    while True:
        to_merge = np.unravel_index(savings_matrix.argmax(), savings_matrix.shape)
        print(to_merge)
        print(savings_matrix[to_merge[0], to_merge[1]])
        if savings_matrix[to_merge[0], to_merge[1]] < 0:
            break
        stop1 = ind_stop_map[to_merge[0]]
        stop2 = ind_stop_map[to_merge[1]]
        route1 = stop_info_map[stop1][1]
        route2 = stop_info_map[stop2][1]
        for stop in route2.stops:
            assert route1.add_stop(stop)
            stop_info_map[stop][1] = route1
        two_opt(route1, report = False)
        assert route1.feasibility_check(verbose = True)
        for i in range(stop_ind_counter):
            for stop_ind in range(len(route1.stops)):
                #Can't just iterate over the list if we are
                #using 2-opt because iteration order is not
                #guaranteed if we modify the list in place,
                #even though we put it back after.
                stop = route1.stops[stop_ind]
                if savings_matrix[stop_info_map[stop][0], i] > -100000:
                    update(stop, ind_stop_map[i], stop_info_map, savings_matrix)
                if savings_matrix[i, stop_info_map[stop][0]] > -100000:
                    update(ind_stop_map[i], stop, stop_info_map, savings_matrix)
    out_routes = set()
    for stop in stop_info_map:
        out_routes.add(stop_info_map[stop][1])
    return list(out_routes)