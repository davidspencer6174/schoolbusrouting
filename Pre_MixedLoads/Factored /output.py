import pandas as pd
import numpy as np 
import pickle
import math
import constants

# Print statistics of a school cluster
def printBeginStats(cluster_school_map, schoolcluster_students_map, cap_counts, school_type):
    
    numStudents = 0 
    numSchools = 0 

    for value in schoolcluster_students_map.values():
        for j in range(0, len(value)):
            numStudents = numStudents + len(value[j])
            
    for value in cluster_school_map.values():
        numSchools = numSchools + len(value)

    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]

    print('--------------------------------------------------------------------')
    print("Starting to route " + school_type.upper() + " SCHOOL students")
    print('PARAMETERS USED')
    print('RADIUS: ' + str(constants.RADIUS))
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
    buses_used = dict({16: 0, 17: 0, 24: 0, 33: 0, 34: 0, 41: 0, 62: 0, 65: 0, 71: 0, 84: 0})
    route_travel_info = list()
    utility_rate = list()
    routesCount = 0 

    for i in routes_returned:
        for j in routes_returned[i]:
            
            routesCount += len(j)
            
            for k in j:
                studentCount += k.occupants

                if k.bus_size in buses_used: 
                    buses_used[k.bus_size] += 1
                    
                utility_rate.append(k.occupants/k.bus_size)
                    
                for x in k.path_info:
                    route_travel_info.append(x)
                                
    total_travel_time = round((sum([i for i, j in route_travel_info])/3600), 2)
    utility_rate = round(np.average(utility_rate), 2)
    average_travel_time = round(total_travel_time*60/routesCount)
    
    print('---------------------------------')
    print('Post-routing statistics')
    print('---------------------------------')
    print("Num. of Students Routed: " + str(studentCount))
    print("Num. of Routes Generated: " + str(routesCount))
    print("Total travel time: " + str(total_travel_time) + " hours" )
    print("Average travel time / route: " + str(average_travel_time) + " minutes")
    print("Utility rate: " + str(utility_rate*100) + "%")
    print("Buses Used: " + str(sum(buses_used.values())))
    print("Bus Info: ")
    print(buses_used)
    print("\n")
    
    output = [studentCount, routesCount, total_travel_time, average_travel_time, utility_rate, buses_used]
    return output
    
# write routes into .txt file
# cluster_school_map: maps clusters to schools
# routes_returned: bus routes for each school cluster
def outputRoutes(cluster_school_map, routes_returned, filename, title):

    prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
    all_geocodesFile = prefix+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)
    output = printFinalStats(routes_returned)

    if constants.REMOVE_LOW_OCC:
        file = open("remove_low_occ_" + str(filename) + ".txt", "w")   
    else:
        file = open(str(filename) + ".txt", "w")   
 
    file.write('---------------------------------\n')
    file.write('ROUTE STATS: ' + str(title) + '\n')
    file.write('---------------------------------\n')
    file.write("LOW OCCUPANCY REMOVAL: " + str(constants.REMOVE_LOW_OCC) + '\n')
    file.write("Num. of Students Routed: " + str(output[0]) + '\n')
    file.write("Num. of Routes Generated: " + str(output[1]) + '\n')
    file.write("Total travel time: " + str(output[2]) + " hours" + '\n')
    file.write("Average travel time / route: " + str(output[3]) + " minutes" + '\n')
    file.write("Utility rate: " + str(output[4]*100) + '%\n')

    for index in range(0, len(routes_returned)):   
        
        file.write("----------------------\n")
        file.write("Cluster Number: " + str(index) + "\n")
        file.write("Schools in this cluster: \n") 
        
        count = 0
        for clus_school in cluster_school_map[index]:            
            file.write(str(clus_school.school_name) +  " (" + str(clus_school.cost_center) + ")"+"\n")
        
        file.write('\n')
        googlemap_routes = list()

        for idx in range(0, len(routes_returned[index])):
            
            for route in routes_returned[index][idx]:
                if int(route.occupants) < 8:
                    file.write("LOW OCCUPANCY BUS \n")
                    
                file.write("Route index: " + str(index) + "." + str(count) + "\n")
                file.write("Route path: " + str(route.path) + "\n")
                file.write("Route path information: " + str(route.path_info) + "\n")
                file.write("Bus capacity: " + str(route.bus_size) + "\n")
                file.write("Num. of occupants: " + str(route.occupants) + "\n\n")
                
                link = "https://www.google.com/maps/dir"
    
                for point in route.path:
                    point_geoloc = geocodes.iloc[point,: ]
                    
                    link += ("/" + str(round(point_geoloc['Lat'],6)) + "," + str(round(point_geoloc['Long'],6)))
                    
                googlemap_routes.append(link)
                file.write("Google Maps Link: \n")
                file.write(link)
                file.write("\n---------------------- \n")
                count += 1
                
        file.write("\n###################################################\n")
        file.write("BULK GOOGLE MAP ROUTES FOR CLUSTER \n")
        for x in googlemap_routes:
            file.write(x)
            file.write("\n")
        file.write("###################################################\n")

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
