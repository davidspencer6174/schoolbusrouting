import pandas as pd
import sys 
from routing import start_routing
from setup import setup_data, setup_clusters
from output import get_route_stats, get_student_stats, plot_histograms
from utilities import find_routes_with_schools
from plot_plotly import plot_routes


def main():
   
    # try: 
    #     if sys.argv[1] == "True": 
    #         constants.REMOVE_LOW_OCC = True
    #     else:
    #         constants.REMOVE_LOW_OCC = False 
    # except: 
    #     pass

    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
    
    schools_students_attend, schoolcluster_students_map_df = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                                        prefix+'zipData.csv', 
                                                                        prefix+'school_geocodes_fixed.csv', 
                                                                        prefix+'totalPhoneBook.csv',
                                                                        prefix+'bell_times.csv')

    cluster_school_map, schoolcluster_students_map = setup_clusters(schools_students_attend, schoolcluster_students_map_df)
    routes_returned = start_routing(cluster_school_map, schoolcluster_students_map)

    # Get statistics 
    utility_rate = get_route_stats(routes_returned, cluster_school_map, schoolcluster_students_map)
    students_travel_times = get_student_stats(routes_returned)
    
    return routes_returned, utility_rate, students_travel_times


routes_returned, utility_rate, students_travel_times = main()

#plot_histograms(students_travel_times, utility_rate)

# school_to_find = ['Combined -- Vintage', [10827]]
# school_to_find = ['Combined -- Balboa', [10376]]
# schools_geo, stops_geo, routes = find_routes_with_schools(routes_returned, school_to_find[1])
#plot_routes(schools_geo, stops_geo, routes, school_to_find[0])


    
    
    



