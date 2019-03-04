import constants
from routing import startRouting
from setup import setup_data, setup_cluster
from output import printBeginStats, outputRoutes, printFinalStats

# School type can be (elem, middle, or high)
def main():
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
    schools_students_attend, schoolcluster_students_map_df = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                                        prefix+'zipData.csv', 
                                                                        prefix+'school_geocodes_fixed.csv', 
                                                                        prefix+'totalPhoneBook.csv',
                                                                        prefix+'bell_times.csv')

    cluster_school_map, schoolcluster_students_map = setup_cluster(schools_students_attend, schoolcluster_students_map_df)
    
    printBeginStats(cluster_school_map, schoolcluster_students_map, constants.CAP_COUNTS, constants.SCHOOL_TYPE)
    routes_returned = startRouting(cluster_school_map, schoolcluster_students_map)
    outputRoutes(cluster_school_map, routes_returned, (str(constants.SCHOOL_TYPE)+"_school_routes"), (constants.SCHOOL_TYPE.upper()+" SCHOOL ROUTES \n"))
    finalStats = printFinalStats(routes_returned)
    
    return routes_returned, finalStats

# TODO: Check how changing eps. of DBSCAN and cluster number of KMEANs 
#       will affect the performance of the routing 
constants.SCHOOL_TYPE = 'elem'
elem_routes, elemStats = main()

constants.SCHOOL_TYPE = 'middle'
middle_routes, midStats = main()

constants.SCHOOL_TYPE = 'high'
high_routes, highStats = main()

