import numpy as np 
import pandas as pd 
import constants
from locations import Route

# Begin routing 
def start_routing(single_school_clusters):
	for idx, _ in enumerate(single_school_clusters):
			single_school_clusters[idx].create_routes_for_cluster()
	return single_school_clusters

# Perform routing for a cluster
def route_cluster(cluster):
	routes_returned = list()
	stops_path_list = list()
	stops_path = list()
	stops_info = get_stops_info(get_possible_stops_path(cluster), cluster)

	last_stop = cluster.school_path[-1]
	for idx, stop in enumerate(stops_info):
		stops_path.append(stop)
		stud_count = (np.array([j[2] for j in stops_path])).sum(axis=0)
		MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[constants.CAP_COUNTS[-1][0]])

		if (cluster.get_school_route_time() + sum([i[1] for i in stops_path]) > constants.MAX_TIME) or \
			((stud_count[0]/MOD_BUS[0])+(stud_count[1]/MOD_BUS[1])+(stud_count[2]/MOD_BUS[2])) > 1:

			last_stop = cluster.school_path[-1]
			if len(stops_path) == 1:
				stops_path_list.append(stops_path)
				stops_path = list()
			else:
				stops_path_list.append(stops_path[:-1])
				stops_path = list()
				stops_path.append((stop[0], round(constants.TRAVEL_TIMES[last_stop][stop[0]], 2), stop[2]))
				last_stop = stop
		else:
			last_stop = stop

	if stops_path:
		stops_path_list.append(stops_path)

	#TODO: add routes to pick up students
	idx = 0 
	while idx < len(stops_path_list):
		new_route = Route(cluster.school_path, stops_path_list[idx])



		new_route.assign_bus_to_route()
		routes_returned.append(new_route)
		idx += 1 

	return routes_returned

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
			dist = round(constants.TRAVEL_TIMES[cluster.school_path[-1]][stop], 2)
		else:
			dist = round(constants.TRAVEL_TIMES[possible_stops_path[idx-1]][stop], 2)

		stop_info = (stop, dist, stop_stud_count)
		stops_info.append(stop_info)
	return stops_info 

# Get possible stops path 
def get_possible_stops_path(cluster):
	stops_path, visited = list(), list()
	index = 0

	total_indexes = [cluster.school_path[-1][0]] + list(set([stud.tt_ind for stud in cluster.students_list]))
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


    