from routing import start_routing, start_combining, clean_and_combine_within_cluster
from setup import setup_data
from output import print_routes
import pickle
import datetime 
from utils import unpack_routes

def main():
   
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
    
    # Setup data
    single_school_clusters = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                        prefix+'zipData.csv', 
                                        prefix+'school_geocodes_fixed.csv', 
                                        prefix+'totalPhoneBook.csv',
                                        prefix+'bell_times.csv')

    # Perform routing 
    clustered_route = start_routing(single_school_clusters)
    combined_clustered_routes = start_combining(clustered_route)
    return combined_clustered_routes

combined_clustered_routes = main()
clean_and_combine_within_cluster(combined_clustered_routes)
unpacked_routes = unpack_routes(combined_clustered_routes)




#
#converted_routes= list()
#for idx in combined_clustered_routes: 
#    for routes in combined_clustered_routes[idx].routes_list:
#        converted_routes.append(convert_to_common(routes))
#
#
#with open('converted_routes('+str(datetime.datetime.now())+')', 'wb') as f:
#    pickle.dump(converted_routes, f, pickle.HIGHEST_PROTOCOL)
    
# print_routes(combined_clustered_routes)
