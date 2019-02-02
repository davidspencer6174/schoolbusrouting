import constants
from locations import Student

#Perform the mixed-load improvement procedure on a list of routes.
#This function does require it to be a list rather than a
#general Iterable, since it deletes while iterating.
def mixed_loads(route_list):
    #Iterate over all routes and check whether they
    #can be removed.
    buses_saved = []
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
                moved = False
                for route_to_add_to in route_list:
                    if (route_to_add_to != route_to_delete and
                        route_to_add_to.add_student(location)):
                        moved = True
                        break
                if not moved:
                    succeeded = False  #We were unable to move this student
                    break
        if not succeeded:  #Couldn't move all students; revert changes
            for route in route_list:
                route.restore()
        else:
            if constants.VERBOSE:
                print("Successfully deleted a route")
            #Track capacities of saved buses
            buses_saved.append(route_to_delete.bus_capacity)
            del route_list[i]
            i -= 1
        i += 1
        #if i > 200:  #for the purposes of obtaining quicker profiling results
        #    break
    print("New number of routes: " + str(len(route_list)))
    return buses_saved