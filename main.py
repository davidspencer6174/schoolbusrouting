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

converted_routes= list()
for route in unpacked_routes: 
    converted_routes.append(convert_to_common(route))


with open('temp.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
    pickle.dump(converted_routes, f, pickle.HIGHEST_PROTOCOL)

#with open('inter_format_post_imp_exp', 'rb') as f:
#    # The protocol version used is detected automatically, so we do not
#    # have to specify it.
#    testing = pickle.load(f)
