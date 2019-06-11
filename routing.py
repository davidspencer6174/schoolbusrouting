import numpy as np 
import constants
from locations import Route
import copy
from collections import defaultdict
from convert_improve import convert_and_improve
import pickle
import random

# Begin routing 
def start_routing(single_school_clusters):
	for idx, _ in enumerate(single_school_clusters):
		print("Processing cluster: " + str(idx))
		single_school_clusters[idx].create_routes_for_cluster()
		print('---------------------------')
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
		# stud_count = (np.array([j[2] for j in stops_path])).sum(axis=0)

		# if constants.CAP_COUNTS:
		# 	MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[max(constants.CAP_COUNTS.keys())])
		# else: 
		# 	MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[max(constants.CAP_COUNTS.keys())])

		if (cluster.get_school_route_time() + sum([i[1] for i in stops_path]) > constants.MAX_TIME):
			#  or \
			# ((stud_count[0]/MOD_BUS[0])+(stud_count[1]/MOD_BUS[1])+(stud_count[2]/MOD_BUS[2])) > 1:

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
		# new_route.assign_bus_to_route()

		# # If no bus can fit students, then split route
		# if new_route.bus_size == 0:
		# 	splitted_routes = split_route(new_route, [])
		# 	routes_returned.extend(splitted_routes)
		# else:
		# 	routes_returned.append(new_route)

		routes_returned.append(new_route)
		idx += 1

#	print('check routes_returned')
#	new_routes = convert_and_improve(routes_returned)
#	print('check new routes')
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

# Use the all pairs combining method
def all_pairs_start_combining(clustered_routes):
	counts_mat, improved_counts = create_init_mat(clustered_routes)
	clusters = combine_clusters(clustered_routes, counts_mat, improved_counts)
	return clusters

# combine clusters based on number of routes produced 
def combine_clusters(clusters, counts_mat, improved_counts):

	improving = True

	while improving:
		# Find index where would improve most  
		begin_num = len(clusters)
		
		num_routes = 0 
		for clus in clusters.values():
			num_routes += len(clus.routes_list)
        
		print("BEGIN: # clusters: " + str(begin_num) + ' -- ' + ' # routes: ' + str(num_routes))
		max_val = max(map(max, improved_counts))
        
		if max_val == 0:
			improving = False
			break

		print("Max val: " + str(max_val))
		pos_indexes = np.where(improved_counts == max_val)
		pos_indexes = np.asarray(pos_indexes).T.tolist() 
		index_to_use = random.choice(pos_indexes)

		# Update clusters and matrices  
		clusters, counts_mat, improved_counts = update_info(index_to_use, clusters, counts_mat, improved_counts)
		end_num = len(clusters)

		num_routes = 0 
		for clus in clusters.values():
			num_routes += len(clus.routes_list)

		print("END: # clusters: " + str(end_num) + ' -- ' + ' # routes: ' + str(num_routes))
		print(' ------------------------- ')
		
	return clusters

def update_info(index_to_use, clusters, counts_mat, improved_counts):
	x, y = index_to_use[0], index_to_use[1]
	new_cluster = copy.deepcopy(clusters[x])
	new_cluster = new_cluster.combine_clusters(copy.deepcopy(clusters[y]))
	clusters[x] = new_cluster
	clusters.pop(y)

	# reindex dictionary
	for i in range(y, max(clusters.keys())):
		clusters[i] = clusters[i+1]
		clusters.pop(i+1)

	counts_mat = np.delete(counts_mat, y, 0)
	counts_mat = np.delete(counts_mat, y, 1)

	count_indexes = list()

	for idx, clus in enumerate(clusters.values()):

		test_cluster = copy.deepcopy(new_cluster)

		if idx == x: 
			count_indexes.append(len(test_cluster.routes_list))
		else:
			test_cluster = test_cluster.combine_clusters(clus)

			if test_cluster:
				count_indexes.append(len(test_cluster.routes_list))
			else: 
				count_indexes.append(np.nan)

	counts_mat[x,:] = list([0] * (x)) + list(count_indexes[x:])
	counts_mat[:,x] = list(count_indexes[:x+1]) + list([0] * (counts_mat.shape[0] - x - 1))
	
	# re-create improved counts matrix 
	n = len(clusters)
	improved_counts = np.zeros((n,n))

	for i in range(0, n):
		for j in range(0,n):
			if i < j: 
				improved_counts[i][j] = counts_mat[i][i] + counts_mat[j][j] - counts_mat[i][j]
			elif i == j:
				improved_counts[i][j] = 0 	 

	return clusters, counts_mat, improved_counts

# Create matrices 
def create_init_mat(clusters):
	# n = len(clusters)
	# counts_mat = np.zeros((n, n))
	# improved_counts = np.zeros((n,n))
		
	# # Create counts matrix 
	# for i in range(0, n):
	#     for j in range(0, n):
	#         print(i,j)
	#         if i < j: 
	#             temp_1 = copy.deepcopy(clusters[i])
	#             temp_2 = copy.deepcopy(clusters[j])
	#             new_cluster = temp_1.combine_clusters(temp_2)
	#             counts_mat[i][j] = return_count_vals(new_cluster)

	#         elif i == j: 
	#             counts_mat[i][j] = len(clusters[i].routes_list)

	# # Create improved counts matrix 
	# for i in range(0, n):
	# 	for j in range(0,n):
	# 		print("Second: " + str((i,j)))
	# 		if i < j: 
	# 			improved_counts[i][j] = counts_mat[i][i] + counts_mat[j][j] - counts_mat[i][j]
	# 		elif i == j:
	# 			improved_counts[i][j] = 0 	

	prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"
	# with open(prefix+"counts_mat.pickle", "wb") as output_file:
	# 	pickle.dump(counts_mat, output_file)

	# with open(prefix+"improved_counts.pickle", "wb") as output_file:
	# 	pickle.dump(improved_counts, output_file)

	with open(prefix+"counts_mat.pickle", "rb") as input_file:
		counts_mat = pickle.load(input_file)

	with open(prefix+"improved_counts.pickle", "rb") as input_file_2:
		improved_counts = pickle.load(input_file_2)
		
	return counts_mat, improved_counts  

# Helper function
def return_count_vals(new_cluster):
	if new_cluster:
		return len(new_cluster.routes_list)
	else:
		return np.nan

# Clean routes
def clean_routes(clustered_routes):
	for clus in clustered_routes.values(): 
		clus.clean_routes_in_cluster()
	return clustered_routes
