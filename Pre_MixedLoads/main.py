import constants
import sys 
from routing import startRouting
from setup import setup_data, setup_cluster
from output import outputRoutes, getRouteStats, getStudentStats

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
    
    for school_category in constants.SCHOOL_CATEGORIES: 
        constants.SCHOOL_TYPE = school_category
        schools_students_attend, schoolcluster_students_map_df = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                                            prefix+'zipData.csv', 
                                                                            prefix+'school_geocodes_fixed.csv', 
                                                                            prefix+'totalPhoneBook.csv',
                                                                            prefix+'bell_times.csv')

        cluster_school_map, schoolcluster_students_map = setup_cluster(schools_students_attend, schoolcluster_students_map_df)
        routes_returned = startRouting(cluster_school_map, schoolcluster_students_map)
        total_routes.append(routes_returned) 

        if constants.VERBOSE:
            finalStats = getRouteStats(routes_returned, schoolcluster_students_map, cluster_school_map)
            getStudentStats(routes_returned)

        outputRoutes(finalStats, routes_returned, (str(school_category)+"_school_routes"), (school_category.upper() + " SCHOOL ROUTES"))

    return routes_returned

total_routes = main()



