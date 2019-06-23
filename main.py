from routing import start_routing, all_pairs_start_combining 
from setup import setup_data
from wh_routestospec import wh_routes_to_spec
from ds_routestospec import spec_to_ds_routes
import ds_constants
from ds_utils import improvement_procedures
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
    clustered_routes = start_routing(single_school_clusters)
    combined_clustered_routes = all_pairs_start_combining(clustered_routes)
    return combined_clustered_routes

combined_clustered_routes = main()
banana = unpack_routes(combined_clustered_routes)

# import pickle
# with open('/users/cuhauwhung/Desktop/two_unpacked_routes.pickle', 'rb') as fp:
#     banana = pickle.load(fp)

spec_routes = wh_routes_to_spec(banana)
ds_routes = spec_to_ds_routes(spec_routes)
#improved_ds = improvement_procedures(ds_routes)

from ds_setup import setup_ds_students, setup_ds_buses
from ds_bus_assignment_brute_force import assign_buses

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_ds_buses(prefix+'dist_bus_capacities.csv')
final_routes = assign_buses(ds_routes, buses)

from ds_diagnostics import metrics 
metrics(final_routes)