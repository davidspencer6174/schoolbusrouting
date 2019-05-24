import constants
from locations import Student, School

#Perform the mixed-load improvement procedure on a list of routes.
#This function does require it to be a list rather than a
#general Iterable, since it deletes while iterating.
def mixed_loads(route_list):
    #Iterate over all routes and check whether they
    #can be removed.
    print("Old number of routes: " + str(len(route_list)))
    i = 0
    while i < len(route_list):
        if (len(route_list) - i) % 50 == 0:
            if constants.VERBOSE:
                print((len(route_list) - i))
        route_to_delete = route_list[i]
        for route in route_list:
            route.backup()
        stops = route_to_delete.stops
        succeeded = True
        for stop in stops:
            added = False
            for route_to_add_to in route_list:
                if route_to_add_to == route_to_delete:
                    continue
                valid_type = True
                for s2 in route_to_add_to.stops:
                    if set([s2.type, stop.type]) == set(['H', 'E']):
                        valid_type = False
                        break
                if valid_type and route_to_add_to.insert_mincost(stop):
                    added = True
                    break
                #If the insertion failed, delete it
                elif stop in route_to_add_to.stops:
                    route_to_add_to.remove_stop(stop)
            if not added:
                succeeded = False
                break
        if succeeded:
            del route_list[i]
            print("Successfully deleted a route")
        else:
            for route in route_list:
                route.restore()
            i += 1