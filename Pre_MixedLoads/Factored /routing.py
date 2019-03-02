import numpy as np
import constants
from collections import Counter
from locations import Route

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "travel_times.npy")

# Precompute possible route based on shortest path
# items: Input schools or students
# index = 0 
# item_indexes: if routing sch., start with empty list. 
#               if routing stud., start with array with closest school
# Returns: route to go through all schools, time it takes to go through route
def getPossibleRoute(items, index, item_indexes):
    
    new_indexes = list()
    route = list()
    time_taken = list()
    visited = list()
        
    # Create the mini travel-time martrix
    [new_indexes.append(it.tt_ind) for it in items]
    new_indexes = list(dict.fromkeys(new_indexes))
    item_indexes.extend(new_indexes)
    route.append(index)
    
    dropoff_mat = [[0 for x in range(len(item_indexes))] for y in range(len(item_indexes))]
    
    for i in range(0, len(dropoff_mat)):
        for j in range(0, len(dropoff_mat[i])):
            dropoff_mat[i][j] = travel_times[item_indexes[i]][item_indexes[j]]  
    
    # Find shorest path through all the stops
    while len(route) < len(dropoff_mat):
        visited.append(index)
        temp = np.array(dropoff_mat[index])
        
        for ind, item in enumerate(temp):
            if ind in visited: 
                temp[ind]=np.nan
            if ind == index:
                temp[ind] = np.nan
        
        # Append the time taken to go from one stop to another in 
        # time taken and stop in route
        time_to_add = np.nanmin(temp)
        index = list(temp).index(time_to_add)
        time_taken.append(time_to_add)
        route.append(index)

    result = list()
    [result.append(item_indexes[i]) for i in route]
    
    return result, time_taken

# TODO: If route doesn't have students that attend specific school, remove school from the route
# Make route objects with route information in them
# Divide routes based on constraints 
def makeRoutes(school_route_time, school_route, stud_route, students):
    
    time = sum(school_route_time)
    path_info_list = list()
    path_info = list()
    base = school_route[-1]
        
    students.sort(key=lambda x: x.tt_ind, reverse=False)
    stop_counts =[stud.tt_ind for stud in students]
    stop_counts = dict(Counter(stop_counts))
        
    # Go through every stop and check if they meet the constants.MAX_TIME or bus constraints
    # Create new route (starting from the schools) if the constraints are not met 
    for index, stop in enumerate(stud_route):
        path_info.append((travel_times[base][stop], stop_counts[stop]))
        
        # If the travel time or the bus capacity doesn't work, then break the routes
        if (time + sum([i for i, j in path_info]) > constants.MAX_TIME) or (sum([j for i, j in path_info]) > constants.CAP_COUNTS[-1][0]):
            base = school_route[-1]
            if len(path_info) == 1:
                path_info_list.append(path_info)
                path_info = list()
                
            else:
                path_info_list.append(path_info[:-1])
                path_info = list()
                path_info.append((travel_times[base][stop], stop_counts[stop]))
        base = stop
    
    # Add the 'leftover' routes back in to the list
    if path_info:
        path_info_list.append(path_info)
            
    # Get the indexs of the schools/stops using path_info_list
    result_list = list()
    ind = 0 
    for group in path_info_list:
        group_list = list()
        for stop in group:
            group_list.append(stud_route[ind])
            ind += 1
        result_list.append(school_route + group_list)
    
    # Stops that might have more students than bus capacity 
    # Break these into different routes
    for idx, path_info_group in enumerate(path_info_list):  
        for stop in path_info_group:   
            if stop[1] > constants.CAP_COUNTS[-1][0]:
                to_update = list()
                temp = (stop[0], constants.CAP_COUNTS[-1][0])
                path_info_group[0] = temp
                to_update.append((stop[0], stop[1] - constants.CAP_COUNTS[-1][0]))                
                result_list.append(result_list[idx])
                path_info_list.append(to_update)
                        
    # Add information about the routes between schools 
    # Prepend travel times from school -> school into the stop_info
    for info in path_info_list:
        for school_time in school_route_time:
            info.insert(0, (school_time, 0))
    
    # Make the route objects and put them into a list 
    route_list = list()
    for index, route in enumerate(result_list):
        current_route = Route(route, path_info_list[index])
        
        # Pick up students at each stop, but if the number of students exceeds 
        # the number of students that should be picked up according to path_info_list 
        # then break 
        for stop in current_route.path:
            for idx, stud in enumerate(students):
                if stud.tt_ind == stop:
                    current_route.add_student(stud)
                    current_route.updateSchoolsToVisit(stud)
                    
                if current_route.occupants >= sum([j for i, j in current_route.path_info]):
                    break

        # Assign buses to the routes according to num. of occupants
        for bus_ind in range(len(constants.CAP_COUNTS)):
            bus = constants.CAP_COUNTS[bus_ind]
            #found the smallest suitable bus
            if current_route.occupants <= bus[0]:
                #mark the bus as taken
                bus[1] -= 1
                current_route.updateBus(bus[0])
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    constants.CAP_COUNTS.remove(bus)
                break
        
        route_list.append(current_route)
    
    # If no students in route attend particular school
    # Remove school from the path and path_info (will decrease length of routes)
    # for route in route_list:
    #     for idx, item in enumerate(route.path):
    #         if item in route.schools_to_visit:
    #             pass
    #         else:
    #             print("Willy")
    #             # route.path.pop(idx)
    #             # route.path_info.pop(idx)
    # print("testing")
    return route_list

# Perform routing 
# cluster_school_map: maps clusters to schools
# schoolcluster_students_map: maps schoolclusters to students
def startRouting(cluster_school_map, schoolcluster_students_map):
    routes = dict()
    # Loop through every cluster of schools and cluster of stops
    # Generate route(s) for each cluster_school and cluster_stops pair
    for key, schools in cluster_school_map.items():
        school_route, school_route_time = getPossibleRoute(schools, 0, [])        
        route_list = list()

        for students in schoolcluster_students_map[key]:
            stud_route = getPossibleRoute(students, 0, [school_route[-1]])[0]
            stud_route.pop(0)
            routes_returned = makeRoutes(school_route_time, school_route, stud_route, students)    
            route_list.append(routes_returned)
            
        routes[key] = route_list        
    return routes