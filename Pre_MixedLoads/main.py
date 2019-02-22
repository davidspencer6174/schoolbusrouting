import pandas as pd
import numpy as np
import numpy.ma as ma
import pickle
from random import randint
from collections import Counter

verbose = 1
stop_point = 10
max_time = 3600

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "travel_times.npy")

class School:
    #tt_ind denotes the index of the school in the travel time matrix
    def __init__(self, tt_ind):
        self.tt_ind = tt_ind

class Student:
    #tt_ind denotes the index of the student's stop in the
    #travel time matrix
    #school_id is the index of the cost center (attendance Co)
    #in the travel time matrix
    #for now, ridership probability is not used
    def __init__(self, tt_ind, school_ind):
        self.tt_ind = tt_ind
        self.school_ind = school_ind
        self.bus_assigned = False

class Route:
    #For now, encapsulated as a list of student/stop index pairs in order
    def __init__(self):
        self.tt_ind = 0
        self.students = []
        self.length = 0
        self.occupants = 0
        self.path = [] 
        
    def __eq__(self, other):
        return self.tt_ind == other.tt_ind and self.tt_ind == other.tt_ind

    def __lt__(self, other):
        return self.tt_ind < other.tt_ind
        
    def get_route_length(self):
        return self.length

    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student):
        self.students.append(student)
        self.occupants += 1
            
    def add_route(self, newroutes):
        self.path.extend(newroutes)
        
    def update_time(self, time):
        self.length += time

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

#prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
#cluster_schools_file = prefix+'elem_clustered_schools_file.csv'
#SC_stops_file = prefix+'clusteredschools_students_map'
#schools_codes_mapFile = prefix+'schools_codes_map'
#stops_codes_mapFile = prefix+'stops_codes_map'
#codes_inds_mapFile = prefix+'codes_inds_map'
#schools_inds_mapFile = prefix+'schools_inds_map'
    
# Setup clusters: input all required files 
def setup_cluster(cluster_schools_file, SC_stops_file, schools_codes_mapFile, stops_codes_mapFile, codes_inds_mapFile, schools_inds_mapFile):
    
    cluster_schools_df = pd.read_csv(cluster_schools_file).drop(['Unnamed: 0'],axis=1)

    with open(SC_stops_file,'rb') as handle:
        schoolcluster_students_df = pickle.load(handle)
    with open(schools_codes_mapFile,'rb') as handle:
        schools_codes_map = pickle.load(handle)
    with open(stops_codes_mapFile ,'rb') as handle:
        stops_codes_map = pickle.load(handle)
    with open(codes_inds_mapFile ,'rb') as handle:
        codes_inds_map = pickle.load(handle)
    with open(schools_inds_mapFile ,'rb') as handle:
        schools_inds_map = pickle.load(handle)

    cluster_school_map = dict()
    for i in list(cluster_schools_df['label'].drop_duplicates()):
        subset = cluster_schools_df.loc[cluster_schools_df['label'] == i].copy()  
        schoollist = []
        for index, row in subset.iterrows():
            cost_center = str(int(row['Cost_Center']))
            school_ind = codes_inds_map[schools_codes_map[cost_center]]
            schoollist.append(School(school_ind))
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

# Print statistics 
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

# Precompute route based on shortest path
# items: Input schools or students
# index = 0 
# item_indexes: if schools, start with empty list. If students, start with array with closest school
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
        

def breakRoutes(time, stud_route, times_required):
    route_list = list()
    
    for stop in stud_route:
        if time + times_required < max_time:

# Perform routing 
def startRouting(cluster_school_map, schoolcluster_students_map):
    
    routes = dict()
    for key, schools in cluster_school_map.items():
        break
        school_route, dropoff_time = getPossibleRoute(schools, 0, [])        
        this_route = Route()
        this_route.add_route(school_route)
        this_route.update_time(sum(dropoff_time))
        route_list = list()
        
        for students in schoolcluster_students_map[key]:
            break
            students.sort(key=lambda x: x.tt_ind, reverse=True)
            stud_route, times_required = getPossibleRoute(students, 0, [this_route.path[-1]])
            stud_route.pop(0)
            times_required.pop(0)
            times_required.extend([0])
            sorted_students = sorted(students, key=lambda x: stud_route.index(x.tt_ind))
            
            new_route = this_route
            student_index = 0
            
            


                
            routes[key] = route_list
            
    return routes
             
def display(students):
    for i in students:
        print(i.tt_ind)
               
# Main()
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
cluster_school_map, schoolcluster_students_map = setup_cluster(prefix+'elem_clustered_schools_file.csv', 
                                                               prefix+'clusteredschools_students_map',
                                                               prefix+'schools_codes_map',
                                                               prefix+'stops_codes_map',
                                                               prefix+'codes_inds_map',
                                                               prefix+'schools_inds_map')

cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
printStats(cluster_school_map, schoolcluster_students_map, cap_counts)
routes_returned = startRouting(cluster_school_map, schoolcluster_students_map)

