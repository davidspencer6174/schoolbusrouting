import constants
from locations import Student, School

#Perform the mixed-load improvement procedure on a list of routes.
#This function does require it to be a list rather than a
#general Iterable, since it deletes while iterating.
def mixed_loads(route_list):
    #Iterate over all routes and check whether they
    #can be removed.
    if constants.VERBOSE:
        print("Old number of routes: " + str(len(route_list)))
    i = 0
    while i < len(route_list):
        if (len(route_list) - i) % 50 == 0:
            if constants.VERBOSE:
                print((len(route_list) - i))
        route_to_delete = route_list[i]
        for route in route_list:
            route.backup("mixed_loads")
        stops = route_to_delete.stops
        succeeded = True
        for stop in stops:
            added = False
            for route_to_add_to in route_list:
                if route_to_add_to == route_to_delete:
                    continue
                if (route_to_add_to.e_no_h and stop.h > 0 and stop.e == 0 or
                    route_to_add_to.h_no_e and stop.e > 0 and stop.h == 0):
                    continue
                if route_to_add_to.insert_mincost(stop):
                    added = True
                    break
            if not added:
                succeeded = False
                break
        if succeeded:
            del route_list[i]
            if constants.VERBOSE:
                print("Successfully deleted a route")
        else:
            for route in route_list:
                route.restore("mixed_loads")
            i += 1