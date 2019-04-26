import pandas as pd

def find_routes_with_schools(routes_returned, schools_to_find):
    
    
    schools_set, stops_set = set(), set()
    
    prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
    all_geocodesFile = prefix+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)

    schools_to_find = set(schools_to_find)
    print("Schools to find: " + str(schools_to_find))
    
    route_list_geo = list()

    for index in range(0, len(routes_returned)):   
        
        count = 0 
        googlemap_routes = list()
        
        for idx in range(0, len(routes_returned[index])):
            
            for route in routes_returned[index][idx]:
                               
                if schools_to_find.issubset(route.schools_to_visit):
                    
                    routes_geo = list()
                    stops_set.update(set(route.get_schoolless_path()))
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
                    
                    googlemap_routes.append(link)
                    route_list_geo.append(routes_geo)
                    print("Google Maps Link: ")
                    print(link)
                    count += 1
            
#        if googlemap_routes:
#            print("###################################################")
#            print("BULK GOOGLE MAP ROUTES FOR CLUSTER")
#            for x in googlemap_routes:
#                print(x)
#            print("###################################################")
    
    
    schools_geo, stops_geo = list(), list()
    
    for school in schools_set: 
        schools_geo.append((geocodes.iloc[school,:]['Lat'], geocodes.iloc[school,:]['Long']))
        
    for stop in stops_set:
        stops_geo.append((geocodes.iloc[stop,:]['Lat'], geocodes.iloc[stop,:]['Long']))
        
#    schools_geo = pd.DataFrame(schools_geo, columns=["Lat", "Long"])
#    stops_geo = pd.DataFrame(stops_geo, columns=["Lat", "Long"])

    return schools_geo, stops_geo, route_list_geo

schools_geo, stops_geo, total_routes_geo = find_routes_with_schools(routes_returned, [10136])
plot_gmap(schools_geo, stops_geo, total_routes_geo)



    
