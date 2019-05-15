import pandas as pd
import pickle
import constants
from locations import Route

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"

with open(prefix+'schoolnames_map.pickle', 'rb') as handle:
    schoolnames_map = pickle.load(handle)
    
#with open(prefix+'routes_returned.pickle', 'rb') as handle:
#    routes_returned = pickle.load(handle)

def find_routes_with_schools(routes_returned, schools_to_find):
        
    all_geocodesFile = prefix+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)

    schools_to_find = set(schools_to_find)
    print("Schools to find: " + str(schools_to_find))
    
    schools_set, stops_set = set(), set()
    routes = list()

    for index in range(0, len(routes_returned)):   
        count = 0 
        googlemap_routes = list()
        
        for route in routes_returned[index]:

            if schools_to_find.issubset(set(route.schools_to_visit)):
                
                routes_geo = list()

                stops_set.update(route.get_schoolless_path())
                schools_set.update(route.schools_to_visit)
                
                print('---------------------------------')
                print("Route index: " + str(index) + "." + str(count))

                if route.is_mixed_loads == True:
                    print("Mixed Loads == True")

                travel_time = 0 
                for route_stat in route.path_info:
                    travel_time += route_stat[0]

                print("Route path: " + str(route.path))
                print("Route travel time: " + str(round(travel_time/60, 2)) +  " mins") 
                print("Route path information: " + str(route.path_info))
                print("Bus capacity: " + str(route.bus_size))
                print("Num. of occupants: " + str(route.occupants))
                link = "https://www.google.com/maps/dir"

                for point in route.path:
                    point_geoloc = geocodes.iloc[point,: ]
                    routes_geo.append((round(point_geoloc['Lat'], 6), (round(point_geoloc['Long'], 6))))
                    link += ("/" + str(round(point_geoloc['Lat'],6)) + "," + str(round(point_geoloc['Long'],6)))
                
                print("Google maps link: ")
                print(str(link))
                googlemap_routes.append(link)
                routes.append(route)
                count += 1
                        
    schools_geo = pd.DataFrame(columns=['Name', 'Lat', 'Long']).round(6)
    for i, school in enumerate(schools_set): 
        schools_geo.loc[i] = [schoolnames_map[school], geocodes.iloc[school,:]['Lat'], geocodes.iloc[school,:]['Long']]
        
    stops_geo = pd.DataFrame(columns=['Lat','Long'])
    for i, stop in enumerate(stops_set):
        stops_geo.loc[i] = ((geocodes.iloc[stop,:]['Lat'], geocodes.iloc[stop,:]['Long']))
        
    return schools_geo, stops_geo, routes


# ROUTE PLAN:
# A route is stored as a 3-tuple (list of stops, list of tt_inds for visited schools, bus capacity)
# A stop is stored as a 2-tuple (tt_ind, set of 2-tuples (school, age_type))

# Convert my route format to intermediate route format 
def convert_to_common(route):
    list_of_stops = list()
    list_of_visited_schools = route.school_path
    bus_capacity = route.bus_size    
    
    for stop in route.get_schoolless_path():

        schools_at_stop = set()
        for stud in route.students:
            if stud.tt_ind == stop:
                schools_at_stop.add((stud.school_ind, stud.age_type))
        
        stops_info = (stop, schools_at_stop)
        list_of_stops.append(stops_info)
    
    route_output = (list_of_stops, list_of_visited_schools, bus_capacity)    
    return route_output 
    
# Convert intermediate route format to my route format 
def convert_from_common(route):
    list_one, list_two, bus_size = route
    path = list_two + [x[0] for x in list_one], 
    path_info = [round(constants.TRAVEL_TIMES[path[idx]][path[idx+1]]/60, 2) for idx, pos in enumerate(path) if idx < len(path)-1]
    output_route = Route(path, path_info, list_two)
    output_route.bus_size = bus_size
    return output_route
    