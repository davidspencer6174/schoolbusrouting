import pandas as pd 
import numpy as n
from collections import defaultdict

def print_routes(clusters):
    school_cluster_counts = defaultdict(int)
    route_count = 0 
    tot_stud_counts = 0 
    for idx in clusters:
        school_cluster_counts[len(clusters[idx].schools_list)] += 1 
#        print("Cluster (" + str(idx) + ") -- " + str([school.school_name for school in clusters[idx].schools_list]))
        for route in clusters[idx].routes_list:
#            print(str(route.schools_path) + str(route.stops_path))
            tot_stud_counts += sum([sum(stop[2]) for stop in route.stops_path])
            
            route_count += 1 
#        print("-----------------------------")
    
#    print("Total Route Counts:" + str(route_count))
#    print("Total Num. Students Routed: " + str(tot_stud_counts))
#    
    return route_count



