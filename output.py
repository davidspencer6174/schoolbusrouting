import pandas as pd 
import numpy as np
from collections import defaultdict
import constants

# Print routes
def print_routes(clusters):
    school_cluster_counts = defaultdict(int)
    route_count = 0 
    for idx in clusters:
        school_cluster_counts[len(clusters[idx].schools_list)] += 1 
        print("Cluster (" + str(idx) + ") -- " + str([school.school_name for school in clusters[idx].schools_list]))
        for route in clusters[idx].routes_list:
            print(str(route.schools_path) + str(route.stops_path))
            route_count += 1 
        print("-----------------------------")
    
    print("Total Rote Counts:" + str(route_count))
    
    

def get_route_stats(routes):
    
    student_times = list()
    bus_size_counts = list()
    
    for route in routes: 
                
        stud_counts = [sum(i) for i in zip(*[x[2] for x in route.stops_path])]
        bus_percent = list()
        for idx, count in enumerate(stud_counts):
            bus_percent.append(count/constants.CAPACITY_MODIFIED_MAP[route.bus_size][idx])
            
        if sum(bus_percent) <= 1: 
            bus_size_counts.append(sum(bus_percent))
        
        for stud in route.students_list :
            student_times.append(stud.time_on_bus)
    
    bus_size_counts = [size*100 for size in bus_size_counts]
    return np.array(student_times), np.array(bus_size_counts)
