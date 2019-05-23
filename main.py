from routing import start_routing, clean_and_combine
from setup import setup_data
from output import print_routes
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
print_routes(clustered_routes)


#with open('routes_returned_(2019-05-22 00:18:47.186591)', 'rb') as f:
#    # The protocol version used is detected automatically, so we do not
#    # have to specify it.
#    explicit_routes = pickle.load(f)
