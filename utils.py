import numpy as np 
import copy
from setup import setup_data

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'
stops = prefix+'stop_geocodes_fixed.csv'
zipdata =prefix+'zipData.csv'
schools = prefix+'school_geocodes_fixed.csv'
phonebook = prefix+'totalPhoneBook.csv'
bell_times = prefix+'bell_times.csv'
setup_data(stops, zipdata, schools, phonebook, bell_times)
#    
#TRAVEL_TIMES = constants.TRAVEL_TIMES
#PHONEBOOK = constants.PHONEBOOK
#GEOCODES = constants.GEOCODES
#SCHOOLS_CODES_MAP = constants.SCHOOLS_CODES_MAP
#CODES_INDS_MAP = constants.CODES_INDS_MAP
#STOPS_CODES_MAP = constants.STOPS_CODES_MAP

# Californication
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

def decaliforniafy(address):
    return address[:-18] + address[-6:]

# unpack routes 
def unpack_routes(clustered_routes):
    unpacked_routes = list()
    for clus in clustered_routes.values():
        unpacked_routes.extend(clus.routes_list)
    return unpacked_routes 

# Return routes for a specific school(s)
def get_routes_for_specific_school(schools, unpacked_routes):
#    unpacked_routes = unpack_routes(clustered_routes)
    routes_to_return = list()
    for route in unpacked_routes:
        if schools.issubset(route.schools_to_visit):
            routes_to_return.append(route)
    return routes_to_return


# Get route statistics
def get_route_stats(routes):
    
    student_times = list()
    bus_size_counts = list()
    sus_routes = list()
    
    new_count = 0 
    
    for idx_0, route in enumerate(routes): 
        
        stud_counts = [sum(i) for i in zip(*[x[2] for x in route.stops_path])]
        
        bus_percent = list()
        for idx, count in enumerate(stud_counts):
            bus_percent.append(round(count/constants.CAPACITY_MODIFIED_MAP[route.bus_size][idx],2))
            
        temp = list()
        for stud in route.students_list:
            print(count) 
            stud.update_time_on_bus(route)
            temp.append(stud.time_on_bus)
            new_count += 1 
        
        if sum(bus_percent) > 1:
            sus_routes.append(('IDX: ' + str(idx_0) + str(route.schools_path) + " -- " + str(route.stops_path)) + " -- " + str(round(max(temp),2)))
        
        student_times.extend(temp)
        
        
    bus_size_counts = [size*100 for size in bus_size_counts]
    return np.array(student_times), np.array(bus_size_counts)

# Fix school types
def fix_school_types(route):

    new_stops = list()
    for idx, stop in enumerate(route[0]):
        school_set = set()
        for idx_2, school in enumerate(stop[1]):
            school_set.add((school[0], constants.SCHOOLTYPE_MAP[school[0]]))
        new_stops.append((stop[0], school_set))
    route_output = (new_stops, route[1], route[2])
    return route_output

    
    
    