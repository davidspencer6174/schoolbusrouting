from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import constants
import numpy as np 
import pandas as pd
from collections import Counter
from itertools import chain
import copy

def create_data_model(travel_times_matrix, time_windows):
  """Stores the data for the problem."""
  data = {}
  data['time_matrix'] = travel_times_matrix 
  data['time_windows'] = time_windows
  data['num_vehicles'] = 2
  data['depot'] = 0
  return data
        
def find_optimal_wait_time(time_windows):
    max_time = 0 
    for i, _ in enumerate(time_windows):
        if i == 0:
            continue
        else: 
            new_time = time_windows[i][0] - time_windows[i-1][1]
            if new_time > max_time:
                max_time = new_time
    return max_time+10

def get_constraints_info(schools_subset):
    schools_subset.drop_duplicates(subset ="tt_ind", keep = 'first', inplace = True) 
    base_time = min(schools_subset.early_start_time)
    schools_subset = schools_subset.sort_values(['early_start_time'], ascending=[True])
    time_windows = list(zip(schools_subset.start_time_seconds.astype(int)-schools_subset.bell_time_intervals.astype(int)-int(base_time), schools_subset.start_time_seconds.astype(int)-int(base_time)))
    dropoff_mat = constants.DF_TRAVEL_TIMES.iloc[schools_subset.tt_ind,:]
    dropoff_mat = dropoff_mat.iloc[:,schools_subset.tt_ind]
    travel_time_matrix = dropoff_mat.values.astype(np.int64).tolist()
    return travel_time_matrix, time_windows

def get_solutions(data, manager, routing, assignment, schools_subset):

    global new_clustered_schools
    global key_count

    total_time = 0
    time_dimension = routing.GetDimensionOrDie('Time')
    total_route_list = list()
    school_indexes = list(schools_subset['tt_ind'])
    
    for vehicle_id in range(data['num_vehicles']):        
        index = routing.Start(vehicle_id)
        plan_output = ''
        list_index = []
        
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += '{0} Time({1},{2}) -> '.format(
                manager.IndexToNode(index), assignment.Min(time_var),
                assignment.Max(time_var))
            
            list_index += [manager.IndexToNode(index)]
            index = assignment.Value(routing.NextVar(index))
        
        time_var = time_dimension.CumulVar(index)
        total_time += assignment.Min(time_var)
        
        if total_time != 0: 
            new_school_route = [school_indexes[i] for i in list_index]
            total_route_list.append(new_school_route)

    counts = Counter(chain(*map(set,total_route_list)))
    total_route_list = [[i for i in sublist if counts[i]==1] for sublist in total_route_list]
    total_route_list[-1] = new_school_route
            
    return total_route_list

def solve_school_constraints(schools_info_df):

    if len(schools_info_df) == 1:
        school_route = [schools_info_df.iloc[0]['tt_ind']]
        return school_route

    else:
        # Get required information 
        travel_time_matrix, time_windows = get_constraints_info(schools_info_df)
        
        # Instantiate the data problem.
        data = create_data_model(travel_time_matrix, time_windows)
        wait_time = int(find_optimal_wait_time(data['time_windows']))

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(
            len(data['time_matrix']), data['num_vehicles'], data['depot'])
    
        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)
    
        # Create and register a transit callback.
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node]
    
        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        time = 'Time'
        routing.AddDimension(
            transit_callback_index,
            wait_time,  # allow waiting time
            constants.MAX_TIME,  # maximum time per vehicle
            False,  # Don't force start cumul to zero.
            time)
        time_dimension = routing.GetDimensionOrDie(time)
        
        # Add time window constraints for each location except depot.
        for location_idx, time_window in enumerate(data['time_windows']):    
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
            
        # Add time window constraints for each vehicle start node.
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(data['time_windows'][0][0],
                                                    data['time_windows'][0][1])
        for i in range(data['num_vehicles']):
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.Start(i)))
            routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(routing.End(i)))
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        assignment = routing.SolveWithParameters(search_parameters)
                    
        # If assignment possible, return school_route 
        if assignment:
            school_route = get_solutions(data, manager, routing, assignment, schools_info_df)
            return school_route 
        else: 
            return False

                 
                  

