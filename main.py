from routing import start_routing, start_combining
from setup import setup_data
from output import print_routes
from utils import unpack_routes, convert_to_common, convert_from_common, get_route_stats
import pickle
import datetime 
import matplotlib.pyplot as plt
from statistics import stdev 

global PHONEBOOK 

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

with open('one_spec.obj', 'rb') as f:
    # The protocol version used is detected automatically, so we do not
    # have to specify it.
    number_one = pickle.load(f)

with open('two_spec.obj', 'rb') as f:
    # The protocol version used is detected automatically, so we do not
    # have to specify it.
    number_two = pickle.load(f)


one_converted_routes= list()
for route in number_one: 
    new_route, PHONEBOOK = convert_from_common(route, PHONEBOOK)
    one_converted_routes.append(new_route)

#
#
#student_times, bus_size_counts = get_route_stats(one_converted_routes)
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










