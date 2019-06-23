from routing import start_routing, clean_and_combine
from setup import setup_data
from output import print_routes
from utils import unpack_routes, convert_to_common
import pickle

def main():
   
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
    
    # Setup data
    clustered_schools = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                   prefix+'zipData.csv', 
                                   prefix+'school_geocodes_fixed.csv', 
                                   prefix+'totalPhoneBook.csv',
                                   prefix+'bell_times.csv')

    # Perform routing 
    clustered_routes = start_routing(clustered_schools)
    return clustered_routes 

clustered_routes = main()
clean_and_combine(clustered_routes)
route_count = print_routes(clustered_routes)

unpacked_routes = unpack_routes(clustered_routes)

from wh_routestospec import wh_routes_to_spec
from ds_routestospec import spec_to_ds_routes
from ds_utils import improvement_procedures

spec_routes = wh_routes_to_spec(unpacked_routes)
ds_routes = spec_to_ds_routes(spec_routes)
#improved_ds = improvement_procedures(ds_routes)

from ds_setup import setup_ds_buses
from ds_bus_assignment_brute_force import assign_buses

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
buses = setup_ds_buses(prefix+'dist_bus_capacities.csv')
final_routes = assign_buses(ds_routes, buses)

from ds_diagnostics import metrics 
metrics(final_routes)
