from routing import start_routing, start_combining
from setup import setup_data
from output import print_routes
import pickle
import datetime 
from utils import unpack_routes, convert_to_common


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
unpacked_routes = unpack_routes(combined_clustered_routes)

converted_routes= list()
for idx in combined_clustered_routes: 
    for routes in combined_clustered_routes[idx].routes_list:
        converted_routes.append(convert_to_common(routes))

# TODO: Use David's post-improvement methods 



#
#
#with open('unpacked_routes('+str(datetime.datetime.now())+')', 'wb') as f:
#    pickle.dump(unpacked_routes, f, pickle.HIGHEST_PROTOCOL)
    
# print_routes(combined_clustered_routes)
