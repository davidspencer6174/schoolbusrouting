import pandas as pd
import numpy as np 
import pickle
import math

# Print statistics of a school cluster
def printBeginStats(cluster_school_map, schoolcluster_students_map, cap_counts, school_type):
    
    numStudents = 0 
    numSchools = 0 

    for key, value in schoolcluster_students_map.items():
        for j in range(0, len(value)):
            numStudents = numStudents + len(value[j])
            
    for key, value in cluster_school_map.items():
        numSchools = numSchools + len(value)

    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]

    print('--------------------------------------------------------------------')
    print("Starting to route " + school_type.upper() + " SCHOOL students")
    print('---------------------------------')
    print('Pre-routing statistics')
    print('---------------------------------')
    print("Num. of Students: " + str(numStudents))
    print("Num. of Schools: " + str(numSchools))
    print("Num. of School Clusters: " +str(len(cluster_school_map)))
    print("Num. of School - Stops Cluster: " + str(len(schoolcluster_students_map)))
    print("Total capacity: " + str(tot_cap) + "\n")
    print("Bus Info: ")
    print(cap_counts)

# TODO: ADD MORE STATISTICS 
# Print statistics after routing complete
def printFinalStats(routes_returned):
    studentCount = 0
    buses_used = dict()
    route_travel_info = list()
    utility_rate = list()
    
    for i in routes_returned:
        for j in routes_returned[i]:
            for k in j:
                studentCount += k.occupants

                if k.bus_size in buses_used: 
                    buses_used[k.bus_size] += 1
                else: 
                    buses_used[k.bus_size] = 0
                    
                utility_rate.append(k.occupants/k.bus_size)
                    
                for x in k.path_info:
                    route_travel_info.append(x)
                    
    routesCount = 0 
    for x in routes_returned:
        for y in routes_returned[x]:
            routesCount += len(y)
            
    print('---------------------------------')
    print('Post-routing statistics')
    print('---------------------------------')
    print("Num. of Students Routed: " + str(studentCount))
    print("Num. of Routes Generated: " + str(routesCount))
    print("Total travel time: " + str(round((sum([i for i, j in route_travel_info])/3600), 2)) + " hours" )
    print("Utility rate: " + str(round(np.average(utility_rate), 2)) + "%")
    print("Bus Info: ")
    print(buses_used)
    print("\n")
    
# write routes into .txt file
# cluster_school_map: maps clusters to schools
# routes_returned: bus routes for each school cluster
def outputRoutes(cluster_school_map, routes_returned, filename, title):

    prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
    all_geocodesFile = prefix+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)

    file = open(str(filename) + ".txt", "w")     
    file.write("######################## \n")
    file.write(title)
    file.write("######################## \n")

    for index, routes_cluster in enumerate(routes_returned):   
        
        file.write("Cluster Number: " + str(index) + "\n")
        file.write("Schools in this cluster: \n") 
        
        count = 0
        for clus_school in cluster_school_map[index]:            
            file.write(str(clus_school.school_name) + "\n")
        
        file.write("\n")
        file.write("Route Stats: ")
        
        for idx, routes in enumerate(routes_returned[index]):
            
            for route_idx, route in enumerate(routes_returned[index][idx]):
                
                file.write("Route index: " + str(index) + "." + str(count) + "\n")
                file.write("Route path: " + str(route.path) + "\n")
                file.write("Route path information: " + str(route.path_info) + "\n")
                file.write("Bus capacity: " + str(route.bus_size) + "\n")
                file.write("Num. of occupants: " + str(route.occupants) + "\n\n")
                
                link = "https://www.google.com/maps/dir"
    
                for point in route.path:
                    point_geoloc = geocodes.iloc[point,: ]
                    
                    link += ("/" + str(point_geoloc['Lat']) + "," + str(point_geoloc['Long']))
                    
                file.write("Google Maps Link: \n")
                file.write(link)
                file.write("\n---------------------- \n")
                count += 1
                    
    file.close()

# Output the clustered objects (schools/stops) with
# their respective geolocations
def outputGeolocationsWithLabels(clustered):
    clustered = clustered.sort_values(by='label')
    file = open("elem_schools_geo" + ".txt", "w") 
    file.write("category,latitude,longitude\n") 

# Write dictionaries to disc
# new_schools: dataframe of clustered schools
# schoolcluster_students_map_df: 
def outputDictionary(schools_students_attend, schoolcluster_students_map_df, student_level):
    schools_students_attend.to_csv(str(student_level) + '_clustered_schools_file.csv', sep=';', encoding='utf-8')
    with open(str(student_level) + '_clusteredschools_students_map' ,'wb') as handle:
        pickle.dump(schoolcluster_students_map_df, handle, protocol=pickle.HIGHEST_PROTOCOL)
