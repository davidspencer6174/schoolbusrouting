import constants
from routing import startRouting
from setup import setup_data, setup_cluster
from output import printBeginStats, outputRoutes, printFinalStats

def main():
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
        outputRoutes(cluster_school_map, routes_returned, (str(school_category)+"_school_routes"), (school_category.upper() + " SCHOOL ROUTES"))

    return routes_returned

total_routes = main()



