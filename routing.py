import numpy as np
import copy
from geopy.distance import geodesic
from operator import add
import constants
from collections import Counter
from locations import Route

# Make last changes to routes before adding to final route list
def check_routes(route_list):
    for route in route_list:
        if constants.CLEAN_ROUTE:
            route.clean_route()
        route.update_student_time_on_bus()
        route.check_mixedload_status()
    return route_list

def unpack_routes(route_list):
    new_route_list = list()
    for route_group in route_list:
        for route in route_group:
            new_route_list.append(route)
    return new_route_list 

def update_times_to_mins(route_list):
    for route in route_list:
        route.update_times_to_mins()
    return route_list

# Make route objects with route information in them
# Divide routes based on constraints 
def make_routes(school_route_time, school_route, stud_route, students):
    
    # total_shool_route_time = time to visit all schools + dropoff time at each school 
    total_school_route_time = sum(school_route_time) + sum([constants.SCHOOL_DROPOFF_TIME[school] for school in school_route])
    path_info = list()
    path_info_list = list()
    last_stop = school_route[-1] 
    
    students.sort(key=lambda x: x.tt_ind, reverse=False)
    
    # Get the categorized student counts at each stop
    stop_counts = dict() 
    for stud in students: 
        if stud.tt_ind in stop_counts:
            stop_counts[stud.tt_ind][stud.student_type] += 1
        else:
            stop_counts[stud.tt_ind] = [0] * 3
            stop_counts[stud.tt_ind][stud.student_type] += 1
    
    # Go through every stop and check if they meet the constants.MAX_TIME or bus constraints
    # Create new route (starting from the schools) if the constraints are not met 
    for index, stop in enumerate(stud_route):
        
        # print('last_stop -- stop: ' + str(last_stop) + ' | ' + str(stop) + ' -- ' + str(constants.TRAVEL_TIMES[last_stop][stop]))
        path_info.append((round(constants.TRAVEL_TIMES[last_stop][stop], 2), stop_counts[stop]))
        stud_count = np.array([j for i,j in path_info])
        sum_stud_count = stud_count.sum(axis=0)
        MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])

        # If the travel time or the bus capacity doesn't work, then break the routes
        if (total_school_route_time + sum([i for i, j in path_info]) > constants.MAX_TIME) or \
            (sum_stud_count[0]/MOD_BUS[0])+(sum_stud_count[1]/MOD_BUS[1])+(sum_stud_count[2]/MOD_BUS[2]) > 1:

            last_stop = school_route[-1]
            if len(path_info) == 1:
                path_info_list.append(path_info)
                path_info = list()

            else:
                path_info_list.append(path_info[:-1])
                path_info = list()
                path_info.append((round(constants.TRAVEL_TIMES[last_stop][stop], 2), stop_counts[stop]))
                last_stop = stop
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
        # the number of students that should be picked up according to path_info_list, break
        for stop in current_route.path:
            for idx, stud in enumerate(students):
                if stud.tt_ind == stop:
                    current_route.add_student(stud)

                if current_route.occupants >= sum(current_route.get_route_occupants_count()):
                    break

        # Assign bus to current route
        current_route.assign_bus_to_route()

        # If there are no buses big enough to fit passengers, we have to split the route and use additional buses
        if current_route.bus_size == None: 
            returned_split_routes = split_route(current_route, [])
            route_list.extend(returned_split_routes)
        else:
            route_list.append(current_route)

    return route_list

# Recursivley split routes that cannot fit into a bus
def split_route(current_route, routes_to_return):

    if current_route.bus_size != None:
        routes_to_return.append(current_route)
        return routes_to_return

    else:
        total_students_list = copy.deepcopy(current_route.students)
        current_route.students = []
        new_route = copy.deepcopy(current_route)

        for i, stop in enumerate(current_route.get_schoolless_path()[::-1]):
            curr_idx = (i+1)*-1
            current_route.path_info[curr_idx] = (current_route.path_info[::-1][i][0], list(map(lambda x: int(x/2), current_route.path_info[::-1][i][1])))
            new_route.path_info[curr_idx] = (current_route.path_info[::-1][i][0], list(np.array(new_route.path_info[::-1][i][1])-np.array(current_route.path_info[::-1][i][1])))
            
            stud_list = list()
            for stud in total_students_list: 
                if stud.tt_ind == stop: 
                    stud_list.append(stud)

            current_route.students.extend(stud_list[:sum(current_route.path_info[curr_idx][1])])
            new_route.students.extend(stud_list[sum(current_route.path_info[curr_idx][1]):])

        current_route.update_occupants()
        current_route.assign_bus_to_route()
        new_route.update_occupants()
        new_route.assign_bus_to_route()

        split_route(current_route, routes_to_return)
        split_route(new_route, routes_to_return)

    return routes_to_return

# find the shortets pair of schools and stops between a school cluster and stop cluster
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
    
    # Make mini-travel-time matrix
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

        for stops_with_students in schoolcluster_students_map[key]:
            shortest_pair = get_shortest_pair(schools, stops_with_students)
            school_route, school_route_time = get_possible_route(schools, shortest_pair[0], [], "school")        
            stud_route = get_possible_route(stops_with_students, shortest_pair[1], [school_route[-1]], "student")[0]
            stud_route.pop(0)
            routes_returned = make_routes(school_route_time, school_route, stud_route, stops_with_students)
            
            if constants.COMBINE_ROUTES:
                combine_routes(routes_returned)
            
            route_list.append(check_routes(routes_returned))

        route_list = unpack_routes(route_list)
        routes[key] = update_times_to_mins(route_list)

    return routes

# Combine routes
def combine_routes(routes):
    
    # routes = copy.deepcopy(input_routes)
    routes_to_check = list()
    # If the route isn't maxed out, insert into routes_to_check
    for route in routes:
        if route.bus_size < constants.CAP_COUNTS[-1][0]: 
            routes_to_check.append(route)

    # If there are no routes_to_check or only one route, just return
    if not routes_to_check or len(routes) == 1: 
        return routes

    # Iterate through routes to check to check if these routes can be combined with existing routes based on conditions
    idx = 0
    while idx < len(routes_to_check):

        # remove route that is currently being checked from original route list
        for temp_route in routes:
            if routes_to_check[idx] == temp_route:
                routes.remove(routes_to_check[idx])
                break
        
        possible_routes = list()
        for pos_route in routes:
            # Set up bus capacity interpolations (x/a + y/b + z/c <= 1)
            MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])
            pos_route_stud_count = pos_route.get_stud_count_in_route()
            routes_to_check_stud_count = routes_to_check[idx].get_stud_count_in_route()
            combined_stud_count = list(map(add, pos_route_stud_count, routes_to_check_stud_count))

            # If is under time and bus capacity interpolation, append into possible route
            if pos_route.get_possible_combined_route_time(routes_to_check[idx]) <= constants.RELAXED_TIME and \
                (combined_stud_count[0]/MOD_BUS[0]) + (combined_stud_count[1]/MOD_BUS[1]) + (combined_stud_count[2]/MOD_BUS[2]) <= 1: 
                 possible_routes.append(pos_route)

        # No possible routes, then append the removed route back into original route list
        if not possible_routes:
            routes += [routes_to_check[idx]]
        else:
            clust_dis = [geodesic(routes_to_check[idx].find_route_center(), a.find_route_center()) for a in possible_routes]
            clust_dis = [round(float(str(a).strip('km')),6) for a in clust_dis]
            ind = [i for i, v in enumerate(clust_dis) if v == min(clust_dis)][0]

            routes.remove(possible_routes[ind]) 
            possible_routes[ind].combine_route(routes_to_check[idx])
            routes.append(possible_routes[ind])
            
        idx += 1

    return routes

