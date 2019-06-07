import pandas as pd 
from collections import defaultdict
import constants
from plot_plotly import plot_routes

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"


# Print routes
def print_routes(clusters):
    school_cluster_counts = defaultdict(int)
    route_count = 0 
    for idx in clusters:
        school_cluster_counts[len(clusters[idx].schools_list)] += 1 
        print("Cluster (" + str(idx) + ") -- " + str([school.school_name for school in clusters[idx].schools_list]))
        for route in clusters[idx].routes_list:
            print(str(route.schools_path) + str(route.stops_path))
            route_count += 1 
        print("-----------------------------")
    
    print("Total Route Counts:" + str(route_count))

# with open(prefix+'schoolnames_map.pickle', 'rb') as handle:
#     schoolnames_map = pickle.load(handle)
    
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
        schools_geo.loc[i] = [constants.SCHOOLNAME_MAP[school], geocodes.iloc[school,:]['Lat'], geocodes.iloc[school,:]['Long']]
        
    stops_geo = pd.DataFrame(columns=['Lat','Long'])
    for i, stop in enumerate(stops_set):
        stops_geo.loc[i] = ((geocodes.iloc[stop,:]['Lat'], geocodes.iloc[stop,:]['Long']))
        
    
    return schools_geo, stops_geo, routes



    

    
