import constants
import pandas as pd
import numpy as np
from locations import School, Student
from clustering import obtainClust_DBSCAN, partitionStudents 

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

# Edit belltimes from ___AM to only seconds
def editBellTimes(schools):
    newTime = list()
    for idx, row in schools.iterrows():        
        if isinstance(row["r1_start"], str):
            hours, mins = row["r1_start"].split(":", 1)
            hours = int(hours)*3600
            mins = int(mins[:2])*60
            newTime.append(hours+mins)
        else:
            newTime.append(np.nan)
    schools['r1_start'] = newTime
    
    return schools

# Set up up the dataframes to make stops, zipdata, schools, and phonebook
# Filter and wrangle through data 
    

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'

stops = prefix+'stop_geocodes_fixed.csv'
zipdata =prefix+'zipData.csv'
schools = prefix+'school_geocodes_fixed.csv'
phonebook = prefix+'totalPhoneBook.csv'
bell_times = prefix+'bell_times.csv'



def setup_data(stops, zipdata, schools, phonebook, bell_times):
    
    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    bell_times = pd.read_csv(bell_times, low_memory=False, encoding='windows-1252')
    schools = pd.read_csv(schools, dtype={'Location_Code': int, 'School_Name': str, 'Cost_Center': int, 'Lat': float, 'Long': float}, low_memory=False)
    schools = schools[['Location_Code', 'School_Name', 'Cost_Center', 'Lat', 'Long']]
    schools = pd.merge(schools, bell_times[['r1_start','Cost_Center']], on ='Cost_Center', how='left')
    
    school_index_list = list()
    for ind, row in schools.iterrows():
        school_index_list.append(constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[str(row['Cost_Center'])]])
    schools['tt_ind'] = school_index_list
    schools = editBellTimes(schools)

    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Prog': str, 'Cost_Center': str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Prog', 'Cost_Center', 'Cost_Center_Name','Grade','AM_Stop_Address', 'AM_Route']]
    phonebook = phonebook[phonebook['AM_Route'] != str(9500)]
    phonebook = phonebook.dropna()
    phonebook = phonebook[phonebook['AM_Stop_Address'] != str(", , ")]
    phonebook = phonebook.dropna()
    phonebook = pd.merge(phonebook, stops[['AM_Stop_Address','Lat', 'Long']], on= 'AM_Stop_Address', how='left')
    
    phonebook["Level"] = None
    mask = (phonebook['Grade'] < 6)
    phonebook['Level'] = phonebook['Level'].mask(mask, "elem")
    mask = (phonebook['Grade'] >= 6) & (phonebook['Grade'] < 9)
    phonebook['Level'] = phonebook['Level'].mask(mask, "middle")
    mask = (phonebook['Grade'] >= 9) & (phonebook['Grade'] <=13)
    phonebook['Level'] = phonebook['Level'].mask(mask, "high")
    
    phonebook = phonebook.loc[phonebook['Level'] == constants.SCHOOL_TYPE]
    phonebook = phonebook[phonebook.Prog.isin(constants.PROG_TYPES)]
    phonebook = phonebook.rename(index=str, columns={"Lat": "Lat", "Long": "Long"})

    schools_students_attend = phonebook["Cost_Center"].drop_duplicates()
    schools_students_attend = schools.loc[schools['Cost_Center'].isin(schools_students_attend)]
    clustered_schools = obtainClust_DBSCAN(schools_students_attend, constants.RADIUS, constants.MIN_PER_CLUSTER)
    
    schools_students_attend = pd.merge(schools_students_attend, clustered_schools, on=['Lat', 'Long'], how='inner').drop_duplicates()
    schools_students_attend = schools_students_attend.sort_values(['label', 'r1_start'], ascending=[True, False])
    
    schoolcluster_students_map_df = partitionStudents(schools_students_attend, phonebook)

    return schools_students_attend, schoolcluster_students_map_df

# Set up the buses
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

# Setup clusters: input all required files 
def setup_cluster(cluster_schools_df, schoolcluster_students_df):
    
    # Cluster to schools map
    cluster_school_map = dict()
    
    for i in list(cluster_schools_df['label'].drop_duplicates()):
        subset = cluster_schools_df.loc[cluster_schools_df['label'] == i].copy()  
        schoollist = []
        for index, row in subset.iterrows():
            cost_center = str(int(row['Cost_Center']))
            school_ind = constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[cost_center]]
            schoollist.append(School(school_ind, cost_center, row['School_Name']))
        cluster_school_map[i] = schoollist

    # School cluster to cluster of studentts map 
    schoolcluster_students_map = dict()
    
    for key, value in schoolcluster_students_df.items():
        list_of_clusters = []
        for val in list(value['label'].drop_duplicates()):
            subset = value.loc[value['label'] == val].copy()  
            student_list = []
            
            for index, row in subset.iterrows():
                stop = californiafy(row['AM_Stop_Address'])
                stop_ind = constants.CODES_INDS_MAP[constants.STOPS_CODES_MAP[stop]]
                cost_center = str(int(row['Cost_Center']))
                school_ind = constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[cost_center]]
                this_student = Student(stop_ind, school_ind)
                student_list.append(this_student)
            list_of_clusters.append(student_list)
        schoolcluster_students_map[key] = list_of_clusters

    return cluster_school_map, schoolcluster_students_map
