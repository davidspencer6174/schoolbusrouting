import pandas as pd 
import numpy as n

def print_routes(clusters):
    route_count = 0 
    for idx in clusters:
        print("Cluster (" + str(idx) + ") -- " + str([school.school_name for school in clusters[idx].schools_list]))
        for route in clusters[idx].routes_list:
            print(str(route.school_path) + str(route.stops_path))
            route_count += 1 
        print("-----------------------------")
    
    print("Total Rote Counts:" + str(route_count))