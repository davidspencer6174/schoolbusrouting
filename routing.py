import numpy as np
import copy
from geopy.distance import geodesic
import constants
from collections import Counter
from locations import Route

# Check routes before adding to final list
def check_routes(route_list):
    for route in route_list:
        if constants.CLEAN_ROUTE:
            route.clean_route()
        route.check_mixedload_status()
    return route_list

# Make route objects with route information in them
# Divide routes based on constraints 
def make_routes(school_route_time, school_route, stud_route, students):
    
    total_school_route_time = sum(school_route_time)
    path_info = list()
    path_info_list = list()
    last_stop = school_route[-1] 
    
    students.sort(key=lambda x: x.tt_ind, reverse=False)
    stop_counts =[stud.tt_ind for stud in students]
    stop_counts = dict(Counter(stop_counts))

    MODIFIED_LARGEST_BUS = (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])[constants.SCHOOL_TYPE_INDEX]

    # Go through every stop and check if they meet the constants.MAX_TIME or bus constraints
    # Create new route (starting from the schools) if the constraints are not met 
    for index, stop in enumerate(stud_route):
        path_info.append((round(constants.TRAVEL_TIMES[last_stop][stop],2), stop_counts[stop]))
        
        # If the travel time or the bus capacity doesn't work, then break the routes
        if (total_school_route_time + sum([i for i, j in path_info]) > constants.MAX_TIME) or \
            (sum([j for i, j in path_info]) > MODIFIED_LARGEST_BUS):

            last_stop = school_route[-1]
            if len(path_info) == 1:
                path_info_list.append(path_info)
                path_info = list()
                
            else:
                path_info_list.append(path_info[:-1])
                path_info = list()
                path_info.append((round(constants.TRAVEL_TIMES[last_stop][stop], 2), stop_counts[stop]))
        
        else:
            last_stop = stop
    
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
    
    temp = path_info_list 

    # Stops that might have more students than bus capacity 
    # Break these into seperate (duplicate) routes
    for idx, path_info_group in enumerate(path_info_list):  
        for stop in path_info_group:   
            if stop[1] > MODIFIED_LARGEST_BUS:
                to_update = list()
                temp = (stop[0], MODIFIED_LARGEST_BUS)
                path_info_group[0] = temp
                to_update.append((stop[0], stop[1] - MODIFIED_LARGEST_BUS))                
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
        current_route = Route(copy.deepcopy(route), copy.deepcopy(path_info_list[index]), copy.deepcopy(school_route))
        
        # Pick up students at each stop, but if the number of students exceeds 
        # the number of students that should be picked up according to path_info_list 
        # then break 
        for stop in current_route.path:
            for idx, stud in enumerate(students):
                if stud.tt_ind == stop:
                    stud.update_time_on_bus(stop, current_route)
                    current_route.add_student(stud)
                    
                if current_route.occupants >= sum([j for i, j in current_route.path_info]):
                    break

        # Assign bus to current route
        current_route.assign_bus_to_route()

        # If there are no buses big enough to fit passengers, we have to split the route and use additional buses
        if current_route.bus_size == None and constants.CAP_COUNTS: 
            split_route = current_route.split_route()
            route_list.append(split_route)
        elif current_route.bus_size : 
            current_route.assign_contract_bus_to_route()
        
        route_list.append(current_route)
       
    return route_list

# find the shortes pair of schools and stops
# return [(school_index, stop_index)]
def get_shortest_pair(schools, students):
    
    school_indexes, stop_indexes = list(), list()
    
    [school_indexes.append(sch.tt_ind) for sch in schools]
    [stop_indexes.append(stud.tt_ind) for stud in students]
    stop_indexes = list(dict.fromkeys(stop_indexes))

    pair_distances = constants.DF_TRAVEL_TIMES.iloc[school_indexes,:]
    pair_distances = pair_distances.iloc[:,stop_indexes]

    s, v = np.where(pair_distances == np.min(pair_distances.min()))
    shortest_pair = list(zip(pair_distances.index[s], pair_distances.columns[v]))
        
    return shortest_pair[0]

# Precompute possible route based on shortest path
def get_possible_route(items, shortest_pair_index, total_indexes, item_type):
    
    index_from_items = list()
    route, time_taken = list(), list()
    visited = list()
    index = 0
    
    # Extract indexes from items (schools/students)
    # Add these extracted indexes and append them into total_indexes
    [index_from_items.append(it.tt_ind) for it in items]
    total_indexes.extend(list(dict.fromkeys(index_from_items)))

    if item_type == 'school' and total_indexes[0] != shortest_pair_index:
        temp = total_indexes.index(shortest_pair_index)
        total_indexes[0], total_indexes[temp] = total_indexes[temp], total_indexes[0]

    route.append(total_indexes[index])
    
    dropoff_mat = constants.DF_TRAVEL_TIMES.iloc[total_indexes,:]
    dropoff_mat = dropoff_mat.iloc[:,total_indexes]
    dropoff_mat = dropoff_mat.values

    # Find shorest path through all the stops
    while len(route) < len(dropoff_mat):
        visited.append(index)
        temp = np.array(dropoff_mat[index])
        
        for ind in range(0, len(temp)):
            if ind in visited: 
                temp[ind]=np.nan
            if ind == index:
                temp[ind] = np.nan
        
        # Append the time taken to go from one stop to another in 
        # time taken and stop in route
        time_to_add = np.nanmin(temp)
        index = list(temp).index(time_to_add)
        time_taken.append(round(time_to_add, 2))
        route.append(total_indexes[index])
   
    if item_type == "school":
         route = route[::-1]

    return route, time_taken

# Perform routing 
# cluster_school_map: maps clusters to schools
# schoolcluster_students_map: maps schoolclusters to students
def start_routing(cluster_school_map, schoolcluster_students_map):
    
    routes = dict()
    # Loop through every cluster of schools and cluster of stops
    # Generate route(s) for each cluster_school and cluster_stops pair
    for key, schools in cluster_school_map.items():
        
        route_list = list()

        for students in schoolcluster_students_map[key]:
            
            shortest_pair = get_shortest_pair(schools, students)
            school_route, school_route_time = get_possible_route(schools, shortest_pair[0], [], "school")        
            stud_route = get_possible_route(students, shortest_pair[1], [school_route[-1]], "student")[0]
            stud_route.pop(0)
            routes_returned = make_routes(school_route_time, school_route, stud_route, students)
            
            if constants.COMBINE_ROUTES:
                routes_returned = combine_routes(routes_returned)

            routes_returned = check_routes(routes_returned)
            route_list.append(routes_returned)
        
        routes[key] = route_list    

    return routes

# Combine routes
def combine_routes(routes):

    routes_to_check = list()

    for route in routes:
        if route.bus_size < (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])[constants.SCHOOL_TYPE_INDEX]: 
            routes_to_check.append(route)

    # If there are no routes_to_check or only one route, just return
    if not routes_to_check or len(routes) == 1: 
        return routes

    # Check if routes can be combined based on size of bus 
    idx = 0
    while idx < len(routes_to_check):

        if routes_to_check[idx].path_info[0] == (3667.2, 1):
            print('willy is here')

        for temp_route in routes:
            if routes_to_check[idx] == temp_route:
                routes.remove(temp_route)
        
        possible_routes = list()
        for pos_route in routes:
            if (routes_to_check[idx].occupants + pos_route.occupants <= (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])[constants.SCHOOL_TYPE_INDEX]) and \
                pos_route.get_possible_combined_route_time(routes_to_check[idx]) <= constants.COMBINE_ROUTES_TIME_LIMIT:
                    possible_routes.append(pos_route)

        if not possible_routes:
            routes.append(routes_to_check[idx])
        
        else:
            clust_dis = [geodesic(routes_to_check[idx].find_route_center(), a.find_route_center()) for a in possible_routes]
            clust_dis = [round(float(str(a).strip('km')),6) for a in clust_dis]
            ind = [i for i, v in enumerate(clust_dis) if v == min(clust_dis)][0]
            
            routes.remove(possible_routes[ind]) 
            possible_routes[ind].combine_route(routes_to_check[idx])
            routes.append(possible_routes[ind])
            
        idx += 1

    return routes

