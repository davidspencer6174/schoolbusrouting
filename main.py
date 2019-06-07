from routing import start_routing, start_combining
from setup import setup_data
from ds_setup import setup_ds_students
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
    clustered_route = start_routing(single_school_clusters)
    combined_clustered_routes = start_combining(clustered_route)
    return combined_clustered_routes

combined_clustered_routes = main()



import pickle
with open('two_spec_pre_improve.obj', 'rb') as fp:
    spec_routes = pickle.load(fp)

from utils import unpack_routes
unpacked_routes = unpack_routes(combined_clustered_routes)
spec_routes = wh_routes_to_spec(unpacked_routes)
ds_routes = spec_to_ds_routes(spec_routes)
improved_routes = improvement_procedures(ds_routes)

from ds_setup import setup_ds_buses
from bus_assignment_brute_force import assign_buses
from ds_diagnostics import diagnostics
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_ds_buses(prefix+'dist_bus_capacities.csv')
assign_buses(improved_routes, buses)
diagnostics(improved_routes)



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

# import pickle
# with open('/users/cuhauwhung/Desktop/two_unpacked_routes.pickle', 'rb') as fp:
#     banana = pickle.load(fp)
