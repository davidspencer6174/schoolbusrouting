from math import sin, cos, sqrt, atan2, radians
import pandas as pd, numpy as np
import pickle 
import csv
from collections import Counter
from math import ceil, floor
import random

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
    #school_id is the index of the cost center (attendance location)
    #in the travel time matrix
    #for now, ridership probability is not used
    def __init__(self, tt_ind, school_ind):
        self.tt_ind = tt_ind
        self.school_ind = school_ind
        self.bus_assigned = False
        
class Route:
    #For now, encapsulated as a list of student/stop index pairs in order
    def __init__(self, tt_ind):
        self.students = []
        self.length = 0
        self.occupants = 0
        self.tt_ind = tt_ind
        self.clusters_visited = [] 
        
    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student, pos = -1):
        self.students = self.students[:pos] + [student] + self.students[pos:]
        if (pos == -1 and len(self.students) > 1) or pos > 0:
            self.length += travel_times[self.students[pos - 1].tt_ind,
                                        self.students[pos].tt_ind]
        if pos > -1 and pos < len(self.students) - 1:
            self.length += travel_times[self.students[pos].tt_ind,
                                        self.students[pos + 1].tt_ind]
        self.occupants += 1
        
    def get_schoolless_route_length(self):
        return self.length
        
    def get_route_length(self):
        return self.length + travel_times[self.students[-1].tt_ind,
                                          self.tt_ind]
        
    def update_visited_clusters(self, cluster_num):
        self.clusers_visited.append(cluster_num)

#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

def setup_students(phonebooks, all_geocodes, geocoded_stops, geocoded_schools):
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    schools = open(geocoded_schools, 'r')
    schools_codes_map = dict()
    schools_students_map = dict()  #maps schools to sets of students
    schools.readline()  #get rid of header
    for cost_center in schools.readlines():
         fields = cost_center.split(";")
         if len(fields) < 8:
             continue
         schools_codes_map[fields[1]] = (fields[6].strip() + ";"
                                         + fields[7].strip())
         schools_students_map[fields[1]] = set()
    schools.close()
    
    geocodes = open(all_geocodes, 'r')
    codes_inds_map = dict()
    ind = 0
    for code in geocodes.readlines():
        codes_inds_map[code.strip()] = ind
        ind += 1
    geocodes.close()
    
    schools_inds_map = dict()
    for school in schools_codes_map:
        schools_inds_map[school] = codes_inds_map[schools_codes_map[school]]
    
    students = []
    bus_col = 12
    for pb_part_filename in phonebooks:
        pb_part = open(pb_part_filename, 'r')
        pb_part.readline()  #header
        for student_record in pb_part.readlines():
            fields = student_record.split(";")
            if len(fields) <= bus_col + 6:
                continue
            if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
                continue
            if fields[bus_col - 1].strip() == "9500":  #walker
                continue
            if fields[bus_col + 2].strip() not in ["1", "01"]:  #not first trip
                continue
            if fields[1].strip() == "":  #no school given
                continue
            #For now, I won't consider special ed.
            #Will be necessary to add later.
            #if fields[5].strip() not in ["M", "X"]:
            #    continue
            stop = californiafy(fields[bus_col + 6])
            school = fields[1].strip()
            stop_ind = codes_inds_map[stops_codes_map[stop]]
            school_ind = codes_inds_map[schools_codes_map[school]]
            this_student = Student(stop_ind, school_ind)
            students.append(this_student)
            schools_students_map[school].add(this_student)
        pb_part.close()
        
    return students, schools_students_map, schools_inds_map
    
def setup_cluster(clusterFile, all_geocodesFile, phonebookFile, schools_inds_map):
    clusters = np.load(clusterFile)
    phonebook = pd.read_csv(phonebookFile, dtype={'stop_Lat': float, 'stop_Long': float}, low_memory=False).drop(['Unnamed: 0'],axis=1)
    phonebook.stop_Lat = round(phonebook.stop_Lat, 6)
    phonebook.stop_Long = round(phonebook.stop_Long, 6)

    geocodes = pd.read_csv(all_geocodesFile).drop(['Unnamed: 0'],axis=1)
    
    cluster_school_map = dict()
    cluster_stops_map = dict()
    stops_students_map = dict()
    
    clusters = clusters.iloc[0]
    schools = pd.DataFrame(sorted(clusters["School_Clustered"], key = lambda x:x[2]))
    stops = pd.DataFrame(sorted(clusters["Stops_Clustered"], key = lambda x:x[2]))
    
    for i in list(schools[2].drop_duplicates()):
        subset = schools[(schools[2] == i)]
        schoollist = []
        for index, row in subset.iterrows():
            lat, long = row[0], row[1]
            index = np.where((geocodes["Lat"] == lat) & (geocodes["Long"] == long))[0][0]
            schoollist.append(School(index))
        cluster_school_map[i] = (schoollist)
            
    for j in list(stops[2].drop_duplicates()):
        subset = stops[(stops[2] == j)]
        stoplist = []
        for index, row in subset.iterrows():
            lat, long = row[0], row[1]
            index = np.where((geocodes["Lat"] == lat) & (geocodes["Long"] == long))[0][0]
            stoplist.append(index)
        cluster_stops_map[j] = (stoplist)
        
    for key, value in cluster_stops_map.items():
        for stop in value:
            studentlist = [] 
            Lat, Long = round(geocodes.iloc[stop]["Lat"],6), round(geocodes.iloc[stop]["Long"],6)
            subset = phonebook[(phonebook.stop_Lat == Lat) & (phonebook.stop_Long == Long)]    
            
            for index, row in subset.iterrows(): 
                stop_ind = stop
                school_ind = schools_inds_map[str(row["Cost_Center"])]
                studentlist.append(Student(stop_ind, school_ind))
            stops_students_map[stop] = studentlist
    return cluster_school_map, cluster_stops_map, stops_students_map

# Start with current cluster and 
def closest_cluster(current_cluster, cluster_stops_map):
    distances = dict()
    cc_random = random.choice(cluster_school_map[current_cluster]).tt_ind
    for temp_cluster in cluster_stops_map:
        tc_random = random.choice(cluster_stops_map[temp_cluster])
        distances[temp_cluster] = travel_times[cc_random][tc_random]
    closest_cluster = min(distances.items(), key=lambda x: x[1]) 
    return closest_cluster[0]

# Find closest stop in a particular cluster, in comparison to current position
def closest_stop(curr_pos, cluster):
    distances = dict()
    for stops in cluster_stops_map[cluster]:
        distances[stops] = travel_times[curr_pos][stops]
    closest_stop = min(distances.items(), key=lambda x: x[1]) 
    return closest_stop[0]

# Routing within a cluster when we reach a particular cluster
def route_within_cluster(curr_loc, cluster, route):

    next_stop = closest_stop(curr_loc, cluster)
    
    
    pass 


def route_cluster(curr_loc, cluster, cluster_school_map, stops_students_map, schools_inds_map):
    
    while True:
        next_cluster = closest_cluster(cluster, cluster_school_map)
        routes_within_cluster = route_within_cluster(curr_loc, next_cluster, Route(curr_loc))
        
        
    return next_cluster 
    
    

# MAIN 
prefix2 = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/data/csvs/"
students, schools_students_map, schools_inds_map = setup_students([prefix2+'phonebook_parta.csv',
                                                                   prefix2+'phonebook_partb.csv'],
                                                                   prefix2+'all_geocodes.csv',
                                                                   prefix2+'stop_geocodes_fixed.csv',
                                                                   prefix2+'school_geocodes_fixed.csv')

prefix3 = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
cluster_school_map, cluster_stops_map, stops_students_map = setup_cluster(prefix3+'clustered_by_levels.p', 
                                                                          prefix3+'w_geocodes.csv', 
                                                                          prefix3+'w_phonebook_split_elem.csv', 
                                                                          schools_inds_map)

print("Number of School Clusters: " +str(len(cluster_school_map)))
print("Number of Stop Clusters: " +str(len(cluster_stops_map)))
print("Number of Students: " + str(sum(len(v[1]) for v in stops_students_map.items())))

for cluster in cluster_school_map:
    random_start = random.choice(cluster_school_map[cluster]).tt_ind
    result = route_cluster(random_start, cluster, cluster_school_map, stops_students_map, schools_inds_map, max_time)



    


        


