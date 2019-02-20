import pandas as pd
import numpy as np
import pickle
from random import randint


verbose = 1
stop_point = 10
max_time = 3600

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "w_travel_times.npy")

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
        
    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student):
        self.students.append(student)
        self.occupants += 1
    
    def get_schoolless_route_length(self):
        return self.length
        
    def get_route_length(self):
        return self.length + travel_times[self.students[-1].tt_ind,
                                          self.tt_ind]
        
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


#cluster_schools_file = prefix+'clustered_schools_file.csv'
#SC_stops_file = prefix+'clusteredschools_students_map'
#all_geocodesFile = prefix+'w_geocodes.csv'
#schools_inds_mapFile = prefix+'schools_inds_map'

def setup_cluster(cluster_schools_file, SC_stops_file, all_geocodesFile, schools_inds_mapFile):
    
    geocodes = pd.read_csv(all_geocodesFile).drop(['Unnamed: 0'],axis=1)
    cluster_schools_df = pd.read_csv(cluster_schools_file).drop(['Unnamed: 0'],axis=1)

    with open(SC_stops_file,'rb') as handle:
        schoolcluster_students_df = pickle.load(handle)
    
    with open(schools_inds_mapFile ,'rb') as handle:
        schools_inds_map = pickle.load(handle)

    cluster_school_map = dict()
    for i in list(cluster_schools_df['label'].drop_duplicates()):
        subset = cluster_schools_df.loc[cluster_schools_df['label'] == i].copy()  
        schoollist = []

        for index, row in subset.iterrows():
            lat, long = row['Lat'], row['Long']
            index = np.where((geocodes["Lat"] == lat) & (geocodes["Long"] == long))[0][0]
            schoollist.append(School(index))
        cluster_school_map[i] = schoollist
        
    schoolcluster_students_map = dict()
    for key, value in schoolcluster_students_df.items():
        list_of_clusters = []
        for val in list(value['label'].drop_duplicates()):
            subset = value.loc[value['label'] == val].copy()  
            student_list = []
            for index, row in subset.iterrows():
                lat, long = row["Lat"], row["Long"]
                stop_ind = np.where((geocodes["Lat"] == lat) & (geocodes["Long"] == long))[0][0]
                school_ind = schools_inds_map[str(row["Cost_Center"])]-2
                this_student = Student(stop_ind, school_ind)
                student_list.append(this_student)
            list_of_clusters.append(student_list)
        schoolcluster_students_map[key] = list_of_clusters
    return cluster_school_map, schoolcluster_students_map

def printStats(cluster_school_map, schoolcluster_students_map, cap_counts):
    numStudents = 0 
    
    for key, value in schoolcluster_students_map.items():
        for j in range(0, len(value)):
            numStudents = numStudents + len(value[j])
             
    print("Number of Students: " + str(numStudents))
    print("Number of School Clusters: " +str(len(cluster_school_map)))
    
    print(cap_counts)
    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]
    print("Total capacity: " + str(tot_cap))

def getSchoolRoute(schools):
    school_route = [] 
    dropoff_time=0 

    dropoff_mat = [[0 for x in range(len(schools))] for y in range(len(schools))]
    for i in range(0, len(dropoff_mat)):
        for j in range(0, len(dropoff_mat[i])):
            dropoff_mat[i][j] = travel_times[schools[i].tt_ind][schools[j].tt_ind]     
            
    visited = set()
    school_route.append(0)
    index = randint(0, len(dropoff_mat))
    
    while len(school_route) < 10:
        visited.add(index)
        temp = np.array(dropoff_mat[index])
        for i in range(0, len(temp)):
            if i in visited:
                temp[i] = 0
        dist_to_add = np.min(temp[np.nonzero(temp)])
        dropoff_time += dist_to_add 
        index = list(temp).index(dist_to_add)
        school_route.append(index)
    return school_route, dropoff_time
    

def studentRoutes():
    pass

    

def startRouting(cluster_school_map, schoolcluster_students_map):
    
    for key, schools in cluster_school_map.items():
        this_route = Route()
        school_route, dropoff_time = getSchoolRoute(schools)
        this_route.add_route(school_route)
        this_route.update_time(dropoff_time)
        
        for newKey, newVal in schoolcluster_students_map.items():
            



# Main()
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
cluster_school_map, schoolcluster_students_map = setup_cluster(prefix+'clustered_schools_file.csv', 
                                                               prefix+'clusteredschools_students_map',
                                                               prefix+'w_geocodes.csv',
                                                               prefix+'schools_inds_map')
cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
printStats(cluster_school_map, schoolcluster_students_map, cap_counts)

routes_returned = startRouting(cluster_school_map, schoolcluster_students_map)

