from routing import start_routing, start_combining
from setup import setup_data
from output import print_routes, get_route_stats
from utils import unpack_routes, convert_to_common
import pickle
import datetime 
import matplotlib.pyplot as plt
from statistics import stdev 

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

#combined_clustered_routes = main()
#unpacked_routes = unpack_routes(combined_clustered_routes)
#
#converted_routes= list()
#for idx in combined_clustered_routes: 
#    for routes in combined_clustered_routes[idx].routes_list:
#        converted_routes.append(convert_to_common(routes))


#with open('routes_returned_(2019-05-22 00:18:47.186591)', 'rb') as f:
#    # The protocol version used is detected automatically, so we do not
#    # have to specify it.
#    explicit_routes = pickle.load(f)

converted_routes= list()
for route in unpacked_routes: 
    converted_routes.append(convert_to_common(route))
#
#with open('unpacked_routes('+str(datetime.datetime.now())+')', 'wb') as f:
#    pickle.dump(unpacked_routes, f, pickle.HIGHEST_PROTOCOL)

with open('unpacked_routes(2019-05-27 20:51:10.458234)', 'rb') as f:
    unpacked_routes = pickle.load(f)

student_times, bus_size_counts = get_route_stats(unpacked_routes)
student_times.mean()
stdev(student_times)

plt.hist(student_times, bins=20)
plt.title('Student travel time distribution (Explicit clustering)')
plt.ylabel('Number of students')
plt.xlabel('Travel time (m)')

plt.hist(bus_size_counts, bins=10)
plt.title('Bus utilization percentage distribution (Pre-defined clustering)')
plt.ylabel('Number of buses')
plt.xlabel('Percentage of capacity occupied')
