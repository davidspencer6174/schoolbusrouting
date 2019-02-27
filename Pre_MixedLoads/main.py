import pandas as pd
import numpy as np
import pickle
from collections import Counter

verbose = 1
stop_point = 10
max_time = 1800

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "travel_times.npy")

class School:
    #tt_ind denotes the index of the school in the travel time matrix
    def __init__(self, tt_ind, cost_center, school_name):
        self.tt_ind = tt_ind
        self.cost_center = cost_center
        self.school_name = school_name

class Student:
    def __init__(self, tt_ind, school_ind):
        self.tt_ind = tt_ind
        self.school_ind = school_ind

class Route:
    #For now, encapsulated as a list of student/stop index pairs in order
    def __init__(self, path, path_info):
        self.students = []
        self.path = path
        self.path_info = path_info
        self.occupants = 0 
        self.bus_size = None
        
    def __eq__(self, other):
        return self.tt_ind == other.tt_ind and self.tt_ind == other.tt_ind

    def __lt__(self, other):
        return self.tt_ind < other.tt_ind
        
    def get_route_length(self):
        return sum([i for i, j in self.path_info])

    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student):
        self.students.append(student)
        self.occupants += 1
    
    def updateBus(self, bus_cap):
        self.bus_size = bus_cap
            
def setup_buses(bus_capacities):
    cap_counts_dict = dict()  #map from capacities to # of buses of that capacity
    caps = open(bus_capacities, 'r')
    for bus in caps.readlines():
        fields = bus.split(";")
        cap = int(fields[1])
        if cap not in cap_counts_dict:
            cap_counts_dict[cap] = 0
        cap_counts_dict[cap] += 1
    caps.close()
    #now turn into a list sorted by capacity
    cap_counts_list = list(cap_counts_dict.items())
    cap_counts_list = sorted(cap_counts_list, key = lambda x:x[0])
    for i in range(len(cap_counts_list)):
        cap_counts_list[i] = list(cap_counts_list[i])
        
    return cap_counts_list

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

# Setup clusters: input all required files 
def setup_cluster(cluster_schools_file, SC_stops_file, schools_codes_mapFile, stops_codes_mapFile, codes_inds_mapFile):
    
    cluster_schools_df = pd.read_csv(cluster_schools_file, sep=";")

    # Input dictionaries 
    with open(SC_stops_file,'rb') as handle:
        schoolcluster_students_df = pickle.load(handle)
    with open(schools_codes_mapFile,'rb') as handle:
        schools_codes_map = pickle.load(handle)
    with open(stops_codes_mapFile ,'rb') as handle:
        stops_codes_map = pickle.load(handle)
    with open(codes_inds_mapFile ,'rb') as handle:
        codes_inds_map = pickle.load(handle)

    cluster_school_map = dict()
    
    for i in list(cluster_schools_df['label'].drop_duplicates()):
        subset = cluster_schools_df.loc[cluster_schools_df['label'] == i].copy()  
        schoollist = []
        for index, row in subset.iterrows():
            cost_center = str(int(row['Cost_Center']))
            school_ind = codes_inds_map[schools_codes_map[cost_center]]
            schoollist.append(School(school_ind, cost_center, row['School_Name']))
        cluster_school_map[i] = schoollist

    schoolcluster_students_map = dict()
    
    for key, value in schoolcluster_students_df.items():
        list_of_clusters = []
        for val in list(value['label'].drop_duplicates()):
            subset = value.loc[value['label'] == val].copy()  
            student_list = []
            
            for index, row in subset.iterrows():
                stop = californiafy(row['AM_Stop_Address'])
                stop_ind = codes_inds_map[stops_codes_map[stop]]
                cost_center = str(int(row['Cost_Center']))
                school_ind = codes_inds_map[schools_codes_map[cost_center]]
                this_student = Student(stop_ind, school_ind)
                student_list.append(this_student)
            list_of_clusters.append(student_list)
        schoolcluster_students_map[key] = list_of_clusters
    return cluster_school_map, schoolcluster_students_map

# Print statistics of a school cluster
def printStats(cluster_school_map, schoolcluster_students_map, cap_counts):
    
    numStudents = 0 
    numSchools = 0 

    for key, value in schoolcluster_students_map.items():
        for j in range(0, len(value)):
            numStudents = numStudents + len(value[j])
            
    for key, value in cluster_school_map.items():
        numSchools = numSchools + len(value)

    print("Number of Students: " + str(numStudents))
    print("Number of Schools: " + str(numSchools))
    print("Number of School Clusters: " +str(len(cluster_school_map)))
    print("Num of School - Stops Cluster: " + str(len(schoolcluster_students_map)))

    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]
    print("Total capacity: " + str(tot_cap))
    print("Bus Info: ")
    print(cap_counts)

# Precompute possible route based on shortest path
# items: Input schools or students
# index = 0 
# item_indexes: if routing sch., start with empty list. 
#               if ruting stud., start with array with closest school
def getPossibleRoute(items, index, item_indexes):
    
    new_indexes = list()
    route = list()
    time_taken = list()
    visited = list()
        
    [new_indexes.append(it.tt_ind) for it in items]
    new_indexes = list(dict.fromkeys(new_indexes))
    item_indexes.extend(new_indexes)
    route.append(index)
    
    dropoff_mat = [[0 for x in range(len(item_indexes))] for y in range(len(item_indexes))]
    
    for i in range(0, len(dropoff_mat)):
        for j in range(0, len(dropoff_mat[i])):
            dropoff_mat[i][j] = travel_times[item_indexes[i]][item_indexes[j]]  
    
    while len(route) < len(dropoff_mat):
        visited.append(index)
        temp = np.array(dropoff_mat[index])
        
        for ind, item in enumerate(temp):
            if ind in visited: 
                temp[ind]=np.nan
            if ind == index:
                temp[ind] = np.nan
        
        time_to_add = np.nanmin(temp)
        index = list(temp).index(time_to_add)
        time_taken.append(time_to_add)
        route.append(index)

    result = list()
    [result.append(item_indexes[i]) for i in route]
    
    return result, time_taken

# Make route objects with route information in them
# Divide routes based on constraints 
def makeRoutes(school_route_time, school_route, stud_route, students):
    
    time = sum(school_route_time)
    path_info_list = list()
    path_info = list()
    base = school_route[-1]
        
    students.sort(key=lambda x: x.tt_ind, reverse=False)
    stop_counts =[stud.tt_ind for stud in students]
    stop_counts = dict(Counter(stop_counts))
        
    # Go through every stop and check if they meet the max_time or bus constraints
    # Create new route (starting from the schools) if the constraints are not met 
    for index, stop in enumerate(stud_route):
        path_info.append((travel_times[base][stop], stop_counts[stop]))
        
        # If the travel time or the bus capacity doesn't work, then break the routes
        if (time + sum([i for i, j in path_info]) > max_time) or (sum([j for i, j in path_info]) > cap_counts[-1][0]):
            base = school_route[-1]
            if len(path_info) == 1:
                path_info_list.append(path_info)
                path_info = list()
                
            else:
                path_info_list.append(path_info[:-1])
                path_info = list()
                path_info.append((travel_times[base][stop], stop_counts[stop]))
        base = stop
    
    # Add the 'leftover' routes back in to the list
    if path_info:
        path_info_list.append(path_info)
            
    # Get the indexs of the schools/stops using path_info_list
    result_list = list()
    ind = 0 
    for group in path_info_list:
        group_list = list()
        for stop in group:
            group_list.append(stud_route[ind])
            ind += 1
        result_list.append(school_route + group_list)
    
    # Stops that might have more students than bus capacity 
    # Break these into different routes
    for idx, path_info_group in enumerate(path_info_list):   
        for stop in path_info_group:   
            if stop[1] > cap_counts[-1][0]:
                to_update = list()
                temp = (stop[0], stop[1] - cap_counts[-1][0])
                path_info_group[0] = temp
                to_update.append((stop[0], cap_counts[-1][0]))                
                result_list.append(result_list[idx])
                path_info_list.append(to_update)
                        
    # Add information about the routes between schools 
    # Prepend travel times from school -> school into the stop_info
    for info in path_info_list:
        for school_time in school_route_time:
            info.insert(0, (school_time, 0))
    
    # Make the route objects and put them into a list 
    route_list = list()
    for index, route in enumerate(result_list):
        current_route = Route(route, path_info_list[index])
        
        # Pick up students at each stop, but if the number of students exceeds 
        # the number of students that should be picked up according to path_info_list 
        # then break 
        for stop in current_route.path:
            
            for idx, stud in enumerate(students):
                if stud.tt_ind == stop:
                    current_route.add_student(stud)
                    
                if current_route.occupants >= sum([j for i, j in current_route.path_info]):
                    break

        # Assign buses to the routes according to num. of occupants
        for bus_ind in range(len(cap_counts)):
            bus = cap_counts[bus_ind]
            #found the smallest suitable bus
            if current_route.occupants <= bus[0]:
                #mark the bus as taken
                bus[1] -= 1
                current_route.updateBus(bus[0])
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    cap_counts.remove(bus)
                break
        
        route_list.append(current_route)
        
    return route_list

# Perform routing 
# cluster_school_map: maps clusters to schools
# schoolcluster_students_map: maps schoolclusters to students
def startRouting(cluster_school_map, schoolcluster_students_map):
    
    routes = dict()
    
    # Loop through every cluster of schools and cluster of stops
    # Generate route for each cluster_school and cluster_stops pair
    for key, schools in cluster_school_map.items():
        school_route, school_route_time = getPossibleRoute(schools, 0, [])        
        route_list = list()

        for students in schoolcluster_students_map[key]:
            stud_route = getPossibleRoute(students, 0, [school_route[-1]])[0]
            stud_route.pop(0)
            routes_returned = makeRoutes(school_route_time, school_route, stud_route, students)    
            route_list.append(routes_returned)
            
        routes[key] = route_list        
    return routes

# write routes into .txt file
# cluster_school_map: maps clusters to schools
# routes_returned: bus routes for each school cluster
def outputRoutes(cluster_school_map, routes_returned, filename, title):
    
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

def start(school_type):
    cluster_school_map, schoolcluster_students_map = setup_cluster(prefix+str(school_type)+'_clustered_schools_file.csv', 
                                                                   prefix+str(school_type)+'_clusteredschools_students_map',
                                                                   prefix+'schools_codes_map',
                                                                   prefix+'stops_codes_map',
                                                                   prefix+'codes_inds_map')
    
    printStats(cluster_school_map, schoolcluster_students_map, cap_counts)
    routes_returned = startRouting(cluster_school_map, schoolcluster_students_map)
    outputRoutes(cluster_school_map, routes_returned, (str(school_type)+"_school_routes"), (school_type.upper()+"SCHOOL ROUTES \n"))
    return routes_returned

##############################################################################################################
# Main()
all_geocodesFile = prefix+'all_geocodes.csv'
geocodes = pd.read_csv(all_geocodesFile)

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')

routes_returned_elem = start('elem')
routes_returned_middle = start('middle')
routes_returned_high = start('high')

count = 0
for i in routes_returned_elem:
    for j in routes_returned_elem[i]:
        for k in j:
            count += k.occupants