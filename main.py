from routing import start_routing, start_combining
from setup import setup_data
from output import print_routes
from utils import convert_to_common, convert_from_common, get_route_stats
import pickle
import matplotlib.pyplot as plt
from statistics import stdev 
import copy

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



#student_times.mean()
#stdev(student_times)
#
#plt.hist(student_times, bins=20)
#plt.title('Student travel time distribution (Explicit clustering)')
#plt.ylabel('Number of students')
#plt.xlabel('Travel time (m)')
#
#plt.hist(bus_size_counts, bins=10)
#plt.title('Bus utilization percentage distribution (Pre-defined clustering)')
#plt.ylabel('Number of buses')
#plt.xlabel('Percentage of capacity occupied')










