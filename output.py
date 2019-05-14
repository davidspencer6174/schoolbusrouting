import pandas as pd 
import numpy as n

def print_routes(clusters):
    print('willy')
    for idx in clusters:
        print("Cluster (" + str(idx) + ")" + str(clusters[idx].schools_list))
        for route in clusters[idx].routes_list:
            print(str(route.school_path) + str(route.stops_path))
        print("-----------------------------")
    pass