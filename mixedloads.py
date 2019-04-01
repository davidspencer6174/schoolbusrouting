import constants
from locations import Student, School

#Perform the mixed-load improvement procedure on a list of routes.
#This function does require it to be a list rather than a
#general Iterable, since it deletes while iterating.
def mixed_loads(route_list):
    #Iterate over all routes and check whether they
    #can be removed.
    num_routes_saved = 0
    print("Old number of routes: " + str(len(route_list)))
    i = 0
    while i < len(route_list):
        if (len(route_list) - i) % 50 == 0:
            if constants.VERBOSE:
                print((len(route_list) - i))
        route_to_delete = route_list[i]
        #Make backups to revert if the deletion fails
        for route in route_list:
            route.backup()
        locations = route_to_delete.locations
        #succeeded will be set to false if we find
        #a student who cannot be moved.
        succeeded = True
        for location in locations:
            #If this is a student, find a route to add to
            if isinstance(location, Student):
                best_cost = 100000
                best_route = None
                for route_to_add_to in route_list:
                    #close_enough_school = False
                    #for loc in route_to_add_to.locations:
                    #    if isinstance(loc, School):
                    #        if (constants.TRAVEL_TIMES[location.school.tt_ind,
                    #                                  loc.tt_ind] < 1000 or
                    #            constants.TRAVEL_TIMES[loc.tt_ind,
                    #                                   location.school.tt_ind] < 1000):
                    #            close_enough_school = True
                    #            break
                    #if not close_enough_school:
                    #    continue
                    route_to_add_to.temp_backup()
                    prev_length = route_to_add_to.length
                    if (route_to_add_to != route_to_delete and
                        route_to_add_to.add_student(location)):
                        cur_cost = route_to_add_to.length - prev_length
                        if cur_cost < best_cost:
                            best_cost = cur_cost
                            best_route = route_to_add_to
                    route_to_add_to.temp_restore()
                if best_route == None:
                    succeeded = False  #We were unable to move this student
                    break
                if not best_route.add_student(location):
                    print("Something went wrong")
        if not succeeded:  #Couldn't move all students; revert changes
            for route in route_list:
                route.restore()
        else:
            if constants.VERBOSE:
                print("Successfully deleted a route")
            #Track number of saved buses
            num_routes_saved += 1
            del route_list[i]
            i -= 1
        i += 1
        #if i > 200:  #for the purposes of obtaining quicker profiling results
        #    break
    print("New number of routes: " + str(len(route_list)))
    return num_routes_saved