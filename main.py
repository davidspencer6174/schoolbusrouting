from routing import start_routing, start_combining
from setup import setup_data
from wh_routestospec import wh_routes_to_spec
from ds_routestospec import spec_to_ds_routes
import ds_constants
from ds_utils import improvement_procedures

def main():
   
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
    
    # Setup data
    single_school_clusters = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                        prefix+'zipData.csv', 
                                        prefix+'school_geocodes_fixed.csv', 
                                        prefix+'totalPhoneBook.csv',
                                        prefix+'bell_times.csv')

    # Perform routing 
#    clustered_route = start_routing(single_school_clusters)
#    combined_clustered_routes = start_combining(clustered_route)
    return combined_clustered_routes

combined_clustered_routes = main()

# converted_routes= list()
# for idx in combined_clustered_routes: 
#     for routes in combined_clustered_routes[idx].routes_list:
#         converted_routes.append(convert_to_common(routes))

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

from ds_setup import setup_buses
from bus_assignment_brute_force import assign_buses

import pickle
with open('/users/cuhauwhung/Desktop/one_unpacked_routes.pickle', 'rb') as fp:
    banana = pickle.load(fp)

spec_routes_banana = wh_routes_to_spec(banana)
ds_routes_banana = spec_to_ds_routes(spec_routes_banana)
improved_banana = improvement_procedures(ds_routes_banana)

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_buses(prefix+'dist_bus_capacities.csv')
final_banana = assign_buses(improved_banana, buses)

# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------

import pickle
with open('/users/cuhauwhung/Desktop/two_unpacked_routes.pickle', 'rb') as fp:
    apple = pickle.load(fp)

spec_routes_apple = wh_routes_to_spec(apple)
ds_routes_apple = spec_to_ds_routes(spec_routes_apple)
improved_apple = improvement_procedures(ds_routes_apple)

from ds_routestospec import ds_routes_to_spec
new_spec_routes = ds_routes_to_spec(improved_apple)

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_buses(prefix+'dist_bus_capacities.csv')
final_apple = assign_buses(improved_apple, buses)

one_final = ds_routes_to_spec(final_banana)
two_final = ds_routes_to_spec(final_apple)


with open('two_final.pickle', 'wb') as handle:
    pickle.dump(two_final, handle, protocol=pickle.HIGHEST_PROTOCOL)








