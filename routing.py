import numpy as np 
import pandas as pd 
import constants
from locations import Route
from geopy.distance import geodesic
import copy
from collections import defaultdict
import math

# Begin routing 
def start_routing(single_school_clusters):
	for idx, _ in enumerate(single_school_clusters):
			single_school_clusters[idx].create_routes_for_cluster()
	return single_school_clusters

# Perform routing for a cluster
def route_cluster(cluster):
	routes_returned = list()
	stops_path_list, stops_path = list(), list()
	stops_info = get_stops_info(get_possible_stops_path(cluster), cluster)
	list_of_students = sorted(copy.deepcopy(cluster.students_list), key=lambda x: [stop[0] for stop in stops_info].index(x.tt_ind))

	last_stop = cluster.schools_path[-1]
	for idx, stop in enumerate(stops_info):
		stops_path.append(stop)
		stud_count = (np.array([j[2] for j in stops_path])).sum(axis=0)

		if constants.CAP_COUNTS:
			MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[max(constants.CAP_COUNTS.keys())])
		else: 
			MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[max(constants.CAP_COUNTS.keys())])

		if (cluster.get_school_route_time() + sum([i[1] for i in stops_path]) > constants.MAX_TIME) or \
			((stud_count[0]/MOD_BUS[0])+(stud_count[1]/MOD_BUS[1])+(stud_count[2]/MOD_BUS[2])) > 1:

			last_stop = cluster.schools_path[-1]
			if len(stops_path) == 1:
				stops_path_list.append(stops_path)
				stops_path = list()
			else:
				stops_path_list.append(stops_path[:-1])
				stops_path = list()
				stops_path.append((stop[0], round(constants.TRAVEL_TIMES[last_stop[0]][stop[0]], 2), stop[2]))
				last_stop = stop
		else:
			last_stop = stop

	if stops_path:
		stops_path_list.append(stops_path)

	idx = 0 
	while idx < len(stops_path_list):
		new_route = Route(cluster.schools_path, stops_path_list[idx], list_of_students)
		new_route.assign_bus_to_route()

		# TODO: CHECK IF THIS IS NEEDED 
		# # If no bus can fit students, then split route
		# if new_route.bus_size == 0:
		# 	splitted_routes = split_route(new_route, [])
		# 	routes_returned.extend(splitted_routes)
		# else:
		# 	routes_returned.append(new_route)

		routes_returned.append(new_route)

		idx += 1 

	return routes_returned

# Recursively split routes
def split_route(current_route, routes_to_return):

	if current_route.bus_size != 0:
		routes_to_return.append(current_route)
		return routes_to_return 

	else:
		total_students_list = copy.deepcopy(current_route.students_list)
		current_route.students_list = []
		new_route = copy.deepcopy(current_route)
		
		for idx, stop in enumerate(current_route.stops_path):
			current_route.stops_path[idx] = (stop[0], stop[1], list(map(lambda x: int(x/2), current_route.stops_path[idx][2])))
			new_route.stops_path[idx] = (stop[0], stop[1], list(np.array(new_route.stops_path[idx][2])-np.array(current_route.stops_path[idx][2])))
			
			stud_list = list()
			for stud in total_students_list: 
				if stud.tt_ind == stop[0]: 
					stud_list.append(stud)
			
			current_route.students_list.extend(stud_list[:sum(current_route.stops_path[idx][2])])
			new_route.students_list.extend(stud_list[sum(current_route.stops_path[idx][2]):])
			
		current_route.assign_bus_to_route()
		new_route.assign_bus_to_route()
		
		split_route(current_route, routes_to_return)
		split_route(new_route, routes_to_return)

	return routes_to_return

# Get student occupancy and travel times
def get_stops_info(possible_stops_path, cluster):
	stops_info = list()

	# Stop info = (stop, [elem_count, middle_count, high_count])
	for idx, stop in enumerate(possible_stops_path):
		stop_stud_count = [0] * 3 
		for stud in cluster.students_list: 
			if stud.tt_ind == stop:
				stop_stud_count[stud.age_type] += 1 

		# Get distance between stops
		if idx == 0:
			dist = round(constants.TRAVEL_TIMES[cluster.schools_path[-1][0]][stop], 2)
		else:
			dist = round(constants.TRAVEL_TIMES[possible_stops_path[idx-1]][stop], 2)

		stop_info = (stop, dist, stop_stud_count)
		stops_info.append(stop_info)
	return stops_info 

# Get possible stops path 
def get_possible_stops_path(cluster):
	stops_path, visited = list(), list()
	index = 0

	total_indexes = [cluster.schools_path[-1][0]] + list(set([stud.tt_ind for stud in cluster.students_list]))
	stops_path.append(total_indexes[index])

	# Setup mini travel time marix
	dropoff_mat = constants.DF_TRAVEL_TIMES.iloc[total_indexes,:]
	dropoff_mat = dropoff_mat.iloc[:,total_indexes]
	dropoff_mat = dropoff_mat.values

	# Find shorest path through all the stops
	while len(stops_path) < len(dropoff_mat):
		visited.append(index)
		temp = np.array(dropoff_mat[index])
		
		for ind in range(0, len(temp)):
			if ind in visited: 
				temp[ind]=np.nan
			if ind == index:
				temp[ind] = np.nan

		# Append the time taken to go from one stop to another in 
		time_to_add = np.nanmin(temp)
		index = list(temp).index(time_to_add)
		stops_path.append(total_indexes[index])

	return stops_path[1:]

# Start combining clusters
def start_combining(clustered_routes):

	count, iter_count = 0, 0 
	index_to_use = 0 

	while True:
		route_counts_for_clusters = list()
		nearest_clusters = clustered_routes[count].find_closest_school_clusters(clustered_routes)
		total_num_of_routes = sum([len(clustered_routes[idx].routes_list) for idx in clustered_routes])
        
		if constants.VERBOSE:
			print('-----------------------')
			print("Iter-count: " + str(iter_count) + " -- Count: " + str(count))
			print("NUM CLUS: " + str(len(clustered_routes)) + " -- NUM OF ROUTES BEGIN: " + str(total_num_of_routes))
		
		# Get statisitcs [(sum_of_seperate, combined_clusters)....()]
		for _, test_clus in enumerate(nearest_clusters):
			
			combined_cluster = clustered_routes[count].combine_clusters(clustered_routes[test_clus[0]])

			if combined_cluster:
				route_counts_for_clusters.append((len(clustered_routes[count].routes_list) + len(clustered_routes[test_clus[0]].routes_list), len(combined_cluster.routes_list)))
				combined_cluster.add_buses_back()
			else:
				route_counts_for_clusters.append((-1,0)) 

		# Once we have obtain the route counts, we check best option and modify clustered_routes_list
		try:
			diff_counters = [i[0]-i[1] if i[1] != None else np.nan for i in route_counts_for_clusters]
			index_to_use = np.nanargmax(diff_counters)

			if diff_counters[index_to_use] > 0: 

				# Remove clus from original dict
				for clus in clustered_routes.values():
					if clus == clustered_routes[nearest_clusters[index_to_use][0]]:

						clustered_routes[count].add_buses_back()
						clustered_routes[count] = copy.deepcopy(clustered_routes[count].combine_clusters(copy.deepcopy(clus)))

						clustered_routes[nearest_clusters[index_to_use][0]].add_buses_back()
						clustered_routes.pop(nearest_clusters[index_to_use][0])

						# Reset keys 
						clustered_routes = {i: clustered_routes[k] for i, k in enumerate(sorted(clustered_routes.keys()))}
						break

				# Break conditions
				end_total_num_of_routes = sum([len(clustered_routes[idx].routes_list) for idx in clustered_routes]) 

				if constants.VERBOSE:
					print("REDUCE AMOUNT: " + str(diff_counters[index_to_use]))
					print("NUMBER OF ROUTES END: " + str(end_total_num_of_routes))

				if end_total_num_of_routes != total_num_of_routes - diff_counters[index_to_use]:
					print("NUMBERS DON'T MATCH UP") 

		# If no combinations
		except ValueError:
			print("VALUE ERROR: No combinations could be done")

		count += 1 

		if count >= len(clustered_routes):
			if total_num_of_routes >= sum([len(clustered_routes[idx].routes_list) for idx in clustered_routes]):
				count = 0
				iter_count += 1
        
		if iter_count == 1:
			break

	return clean_routes(clustered_routes)

# Clean routes
def clean_routes(clustered_routes):
    for clus in clustered_routes.values(): 
        clus.clean_routes_in_cluster()
    return clustered_routes