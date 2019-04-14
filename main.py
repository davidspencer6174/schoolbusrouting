import constants
import sys 
from routing import start_routing
from setup import setup_data, setup_clusters
from output import output_routes_to_file, get_route_stats, get_student_stats

def main():
   
    # try: 
    #     if sys.argv[1] == "True": 
    #         constants.REMOVE_LOW_OCC = True
    #     else:
    #         constants.REMOVE_LOW_OCC = False 
    # except: 
    #     pass

    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
    total_routes = list()
    total_students_travel_times = list()
    
    schools_students_attend, schoolcluster_students_map_df = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                                        prefix+'zipData.csv', 
                                                                        prefix+'school_geocodes_fixed.csv', 
                                                                        prefix+'totalPhoneBook.csv',
                                                                        prefix+'bell_times.csv')

    cluster_school_map, schoolcluster_students_map = setup_clusters(schools_students_attend, schoolcluster_students_map_df)
    routes_returned = start_routing(cluster_school_map, schoolcluster_students_map)

    final_stats = get_route_stats(routes_returned, cluster_school_map, schoolcluster_students_map)
    students_travel_times = get_student_stats(routes_returned)
    output_routes_to_file(final_stats, routes_returned, ("school_routes"), ("SCHOOL ROUTES"))

    total_routes.append(routes_returned)
    total_students_travel_times.append(students_travel_times)

    return total_routes, total_students_travel_times

total_routes, student_travel_times = main()

