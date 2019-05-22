from routing import start_routing, start_combining
from setup import setup_data
from output import print_routes
import pickle
import datetime 

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
