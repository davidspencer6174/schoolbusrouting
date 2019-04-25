import pandas as pd
import constants
import sys 
from routing import start_routing
from setup import setup_data, setup_clusters
from output import output_routes_to_file, get_route_stats, get_student_stats
import statistics 

def main():
   
    # try: 
    #     if sys.argv[1] == "True": 
    #         constants.REMOVE_LOW_OCC = True
    #     else:
    #         constants.REMOVE_LOW_OCC = False 
    # except: 
    #     pass

    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
    
    schools_students_attend, schoolcluster_students_map_df = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                                        prefix+'zipData.csv', 
                                                                        prefix+'school_geocodes_fixed.csv', 
                                                                        prefix+'totalPhoneBook.csv',
                                                                        prefix+'bell_times.csv')

    cluster_school_map, schoolcluster_students_map = setup_clusters(schools_students_attend, schoolcluster_students_map_df)
    routes_returned = start_routing(cluster_school_map, schoolcluster_students_map)

    
    # Get statistics 
    final_stats = get_route_stats(routes_returned, cluster_school_map, schoolcluster_students_map)
    students_travel_times = get_student_stats(routes_returned)
    
    return final_stats, routes_returned, students_travel_times

final_stats_df = pd.DataFrame()

#for rad in range(600, 1800, 60):

rad = constants.RADIUS
constants.REFRESH_STATS()
final_stats, routes_returned, students_travel_times = main()
#final_stats = [constants.RADIUS] + final_stats + [students_travel_times]
#final_stats_df = final_stats_df.append(pd.Series(final_stats, index =['radius,', 'student_count', 'routes_count', 'total_travel_time', 'average_travel_time', 'utility_rate', 'buses_used', 
#               'len(cluster_school_map)', 'len(schoolcluster_students_map)', 'num_combined_routes', 'exceeded_routes', 'num_schools', 'num_mixed_routes', 'student_travel_times']), ignore_index=True)
#

    
    
    



