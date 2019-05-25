import pandas as pd 
import numpy as n
from collections import defaultdict

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