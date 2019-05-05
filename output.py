import pandas as pd
import numpy as np 
import pickle
import constants
import statistics
import matplotlib.pyplot as plt

# Output the clustered objects (schools/stops) with
# their respective geolocations
def output_geo_with_labels(clustered):
    clustered = clustered.sort_values(by='label')
    file = open("test" + ".txt", "w") 
    file.write("label, category,latitude,longitude\n") 
    
    for row in clustered.iterrows():
        file.write(str(row[1]['label']) + "--" + str(row[1]['School_Name']) + "(" + str(row[1]['School_type']) + ":" + str(row[1]['tt_ind']) +")" \
                   + "," + str(row[1]['label'])  +  ", " + \
                   str(row[1]['Lat']) + "," + str(row[1]['Long']) + "\n")

# Write dictionaries to disc
# new_schools: dataframe of clustered schools
# schoolcluster_students_map_df: 
def output_dictionary(schools_students_attend, schoolcluster_students_map_df, student_level):
    schools_students_attend.to_csv(str(student_level) + '_clustered_schools_file.csv', sep=';', encoding='utf-8')
    with open(str(student_level) + '_clusteredschools_students_map' ,'wb') as handle:
        pickle.dump(schoolcluster_students_map_df, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Print statistics of a school cluster
def print_begin_stats(cluster_school_map, schoolcluster_students_map, cap_counts, school_type):
    
    num_students = 0 
    num_schools = 0 

    for value in schoolcluster_students_map.values():
        for j in range(0, len(value)):
            num_students = num_students + len(value[j])
            
    for value in cluster_school_map.values():
        num_schools = num_schools + len(value)

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
    print("Num. of Students: " + str(num_students))
    print("Num. of Schools: " + str(num_schools))
    print("Num. of School Clusters: " +str(len(cluster_school_map)))
    print("Num. of School - Stops Cluster: " + str(len(schoolcluster_students_map)))
    print("Total capacity: " + str(tot_cap) + "\n")
    print("Bus Info: ")
    print(cap_counts)

# Print statistics after routing complete
def get_route_stats(routes_returned, cluster_school_map, schoolcluster_students_map):
    
    # Initialization
    buses_used = dict({16: 0, 17: 0, 24: 0, 33: 0, 34: 0, 41: 0, 62: 0, 65: 0, 71: 0, 84: 0})
    route_travel_info, utility_rate, exceeded_routes, exceeded_routes_times = list(), list(), list(), list()
    student_count, routes_count, num_students, num_schools, num_combined_routes, num_mixed_routes = 0, 0, 0, 0, 0, 0 
    
    for i in routes_returned:
        for route in routes_returned[i]:

            routes_count += 1
            student_count += route.occupants
            
            if route.get_route_length() >= round(constants.MAX_TIME/60,2): 
                exceeded_routes.append(route)
                exceeded_routes_times.append(round(route.get_route_length(), 2))
                
            if route.bus_size in buses_used: 
                buses_used[route.bus_size] += 1
               
            if route.is_combined_route == True:
                num_combined_routes +=1 

            if route.is_mixed_loads == True:
                num_mixed_routes += 1
                    
            for x in route.path_info:
                route_travel_info.append(x)
                
            stud_counts = route.get_route_occupants_count()   
            new_bus = constants.CAPACITY_MODIFIED_MAP
            util_rate = stud_counts[0]/new_bus[route.bus_size][0] + stud_counts[1]/new_bus[route.bus_size][1] + stud_counts[2]/new_bus[route.bus_size][2]
            utility_rate.append(util_rate)
            
    total_travel_time = round((sum([i for i, j in route_travel_info])/60), 2)
    average_travel_time = round(total_travel_time*60/routes_count, 2)

    for value in schoolcluster_students_map.values():
        for j in range(0, len(value)):
            num_students = num_students + len(value[j])
            
    for value in cluster_school_map.values():
        num_schools = num_schools + len(value)
 
    print('---------------------------------')
    print('Schools routing statistics')
    print('---------------------------------')
    print('[PARAMETERS USED]')
    print('Radius: ' + str(constants.RADIUS))
    print('Max time constraint: ' + str(round(constants.MAX_TIME/60, 2)) + ' mins')
    print('Combine route time limit: ' + str(round(constants.RELAX_TIME/60, 2)) + ' mins')
    print(' - - - - - - - - - - - - - - - - -')
    print('[ROUTE STATS]')
    print("Num. of students routed: " + str(student_count))
    print("Num. of routes generated: " + str(routes_count))
    print("Num. of mixed-load routes: " + str(num_mixed_routes))
    print("Num. of schools: " + str(num_schools))
    print("Num. of school clusters: " +str(len(cluster_school_map)))
    print("Total travel-time: " + str(total_travel_time) + " hours" )
    print("Average travel time / route: " + str(average_travel_time) + " mins")
    print("Buses used: " + str(sum(buses_used.values())))
    print(buses_used)
    print("Buses left: ") 
    print(dict(constants.CAP_COUNTS))

    if constants.COMBINE_ROUTES:
        print(' - - - - - - - - - - - - - - - - -')
        print('[COMBINED ROUTE STATS]') 
        print("Num. of combined routes: " + str(num_combined_routes))
        print("Num. of routes that exceed time limit: " + str(len(exceeded_routes)))
        print("Average time of exceeded routes: " + str(round((statistics.mean(exceeded_routes_times)-(constants.MAX_TIME/60)), 2)) + " minutes")
        print("Max exceeded route time: " + str(max(exceeded_routes_times)))
        print("Exceeded route times (mins): " + str(exceeded_routes_times))
        
    else: 
        print(' - - - - - - - - - - - - - - - - -')
        print('[OTHER STATS]') 
        print("Average time of exceeded routes: " + str(round((statistics.mean(exceeded_routes_times)-(constants.MAX_TIME/60)), 2)) + " mins")
        print("Max exceeded route time: " + str(max(exceeded_routes_times)) + ' mins')
        print("Exceeded route times (mins): " + str(exceeded_routes_times))

    
    output = [student_count, routes_count, total_travel_time, average_travel_time, utility_rate, buses_used, 
              cluster_school_map, schoolcluster_students_map, num_combined_routes, exceeded_routes, exceeded_routes_times, 
              num_schools, num_mixed_routes]
    
    if constants.OUTPUT_TO_FILE:

        output_routes_to_file(output, routes_returned, ("school_routes"), ("SCHOOL ROUTES"))
    
    # final_stats = [student_count, routes_count, total_travel_time, average_travel_time, utility_rate, buses_used, 
    #                 len(cluster_school_map), len(schoolcluster_students_map), num_combined_routes, exceeded_routes, num_schools, num_mixed_routes]    
    
    return output
    
# write routes into .txt file
# cluster_school_map: maps clusters to schools
# routes_returned: bus routes for each school cluster
def output_routes_to_file(output, routes_returned, filename, title):
    
    all_geocodesFile = constants.PREFIX+'all_geocodes.csv'
    geocodes = pd.read_csv(all_geocodesFile)

    if constants.COMBINE_ROUTES:
        file = open("combine_route_" + str(filename) + ".txt", "w")   
    else:
        file = open("normal_" + str(filename) + ".txt", "w")   
    
    file.write('---------------------------------\n')
    file.write( str(title) + '\n')
    file.write('---------------------------------\n')
    file.write('[PARAMETERS USED] \n')
    file.write('Radius: ' + str(constants.RADIUS) + '\n')
    file.write('Max time constraint: ' + str(round(constants.MAX_TIME/60, 2)) + ' mins \n')
    file.write("Combine route: " + str(constants.COMBINE_ROUTES) + '\n')

    if constants.COMBINE_ROUTES:
        file.write('Combine route time limit: ' + str(round(constants.RELAX_TIME/60, 2)) + ' mins \n')

    file.write(' - - - - - - - - - - - - - - - - -\n')
    file.write('[ROUTE STATS] \n')
    file.write("Num. of students routed: " + str(output[0]) + '\n')
    file.write("Num. of routes generated: " + str(output[1]) + '\n')
    file.write("Num. of mixed load routes: " + str(output[12]) + '\n')
    file.write("Num. of schools: " + str(output[11]) + '\n')
    file.write("Num. of school clusters: " + str(len(output[6])) + '\n')
    file.write("Total travel time: " + str(output[2]) + " hours" + '\n')
    file.write("Average travel time / route: " + str(output[3]) + " mins" + '\n')

    if constants.COMBINE_ROUTES:
        file.write(' - - - - - - - - - - - - - - - - -\n')
        file.write('[COMBINED ROUTE STATS] \n') 
        file.write("Num. of combined routes: " + str(output[8]) + '\n')
        file.write("Average time of exceeded routes: " + str(round((statistics.mean(output[10])-(constants.MAX_TIME/60)), 2)) + " mins \n")
        file.write("Max exceeded route time: " + str(max(output[10])) + ' mins \n')
        file.write("Exceeded route times (mins): " + str(output[10])+ '\n\n')
    
    else: 
        file.write(' - - - - - - - - - - - - - - - - -\n')
        file.write('[OTHER STATS] \n') 
        file.write("Average time of exceeded routes: " + str(round((statistics.mean(output[10])-(constants.MAX_TIME/60)), 2)) + " mins \n")
        file.write("Max exceeded route time: " + str(max(output[10])) + ' mins \n')
        file.write("Exceeded route times (mins): " + str(output[10])+ '\n\n')


    file.write("----------------------\n")
    file.write("[OUTPUT ROUTES] \n" )

    # Start outputting route information 
    for index in range(0, len(routes_returned)):   
        
        file.write("----------------------\n")
        file.write("Cluster Number: " + str(index) + "\n")
        file.write("Schools in this cluster: \n") 
        
        temp = 0 
        count = 0
        
        school_ages = set()
        for clus_school in output[6][index]:    
            sch_index = constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[clus_school.cost_center]]
            sch_age_type = constants.SCHOOLTYPE_MAP[constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[clus_school.cost_center]]]
            file.write(str(clus_school.school_name) +  " (" + str(clus_school.cost_center) + ") -- " + str(sch_index) + " -- {" + str(sch_age_type) + "}\n")
            school_ages.add(sch_age_type)
            
        file.write('School age categories: ' + str(school_ages) + '\n')
        
        file.write('\n')
        googlemap_routes = list()
        temp_set = set()
        for route in routes_returned[index]:

            temp_set.update(set(route.get_schoolless_path()))

            if int(route.occupants) < constants.UNDER_UTILIZED_COUNT:
                file.write("UNDER UTILIZED BUS \n")
            
            if route.is_combined_route == True:
                file.write("Combined Route == True\n")
            
            if route.is_mixed_loads == True:
                file.write("Mixed Loads == True\n")

            file.write("Route index: " + str(index) + "." + str(count) + "\n")
            file.write("Route path: " + str(route.path) + "\n")
            file.write("Schools to visit: " + str(sorted(list(route.schools_to_visit), key=lambda x: route.school_path.index(x))) + "\n")
            file.write("School drop-off time: " + str(round(route.get_total_school_dropoff_time()/60, 2)) + " mins\n")
            file.write("Route travel time: " + str(round(route.get_route_length(), 2)) +  " mins\n") 
            file.write("TOTAL TIME: " + str(round(route.get_route_length() + route.get_total_school_dropoff_time()/60,2)) + " mins\n")
            file.write("Route path information: " + str(route.path_info) + "\n")
            file.write("Bus capacity: " + str(route.bus_size) + "\n")
            file.write("Num. of occupants: " + str(route.occupants) + "\n")
            link = "https://www.google.com/maps/dir"
            
            temp += len(route.students)

            for point in route.path:
                point_geoloc = geocodes.iloc[point,: ]
                
                link += ("/" + str(round(point_geoloc['Lat'],6)) + "," + str(round(point_geoloc['Long'],6)))
                
            googlemap_routes.append(link)
            file.write("Google Maps Link: \n")
            file.write(link)
            file.write("\n---------------------- \n")
            count += 1

        file.write(" CHECKING STOPS ROUTED \n" )
        file.write(str(sorted(list(temp_set))) + "\n")
        file.write(str(sorted(list(constants.STUDENT_CLUSTER_COUNTER[index]))) + "\n")

        file.write("\n###################################################\n")
        file.write("BULK GOOGLE MAP ROUTES FOR CLUSTER \n")
        for x in googlemap_routes:
            file.write(x)
            file.write("\n")
        file.write("###################################################\n")
    file.close()

# Print out student statistics
def get_student_stats(total_routes): 
    student_travel_times = list()

    for i in total_routes: 
        for route in total_routes[i]:
            for stud in route.students:
                student_travel_times.append(round(stud.time_on_bus, 2))

    student_travel_times.sort() 
    print('----------------------------------') 
    print("Student travel time mean: " + str(round(statistics.mean(student_travel_times),2)) + " mins")
    print("Student travel time stdev: " + str(round(statistics.stdev(student_travel_times), 2)))
    print(" ")
    
    return student_travel_times

def plot_histograms(students_travel_times, utility_rate):
    plt.title('Estimated travel times for generated routes')
    plt.xlabel('Estimated travel time (minutes)')
    plt.ylabel('Number of students')
    plt.hist(students_travel_times, bins=18)
    
    utility_rate = [x * 100 for x in utility_rate]
    plt.title('Distribution of bus utilization percentages (generated)')
    plt.xlabel('Perecent of capcaity used')
    plt.ylabel('Number of routes')
    plt.hist(utility_rate, bins=20)
