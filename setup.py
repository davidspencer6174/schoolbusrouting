import pandas as pd
import numpy as np
import copy
import constants
from locations import Cluster
from clustering import obtainClust_DBSCAN_AGGO_combined, partition_students
from collections import defaultdict
from constraint_solver import solve_school_constraints

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

# Edit belltimes from ___AM to only seconds
def edit_bell_times(schools):
    newTime = list()
    for row in schools.iterrows():        
        if isinstance(row[1]["start_time"], str):
            hours, mins = row[1]["start_time"].split(":", 1)
            hours = int(hours)*3600
            mins = int(mins[:2])*60
            newTime.append(hours+mins)
        else:
            newTime.append(np.nan)
    schools['start_time_seconds'] = newTime
    return schools

# For verification purposes
def update_verif_counters(schoolcluster_students_map_df):
    cluster_counter_dict = dict()
    stop_counter_dict = defaultdict(int)
    
    for i in schoolcluster_students_map_df:
        stop_set = set()

        for _, row in schoolcluster_students_map_df[i].iterrows():
            stop = constants.CODES_INDS_MAP[constants.STOPS_CODES_MAP[californiafy(row['AM_Stop_Address'])]]
            stop_set.add(stop)
            stop_counter_dict[stop] += 1

        cluster_counter_dict[i] = stop_set
        
    constants.STUDENT_CLUSTER_COUNTER = cluster_counter_dict 
    constants.STUDENT_STOP_COUNTER = stop_counter_dict 

# For school dropoff information purposes 
def update_school_dropoff_info(schools_students_attend):
    
    dropoff_dict = dict()
    dropoff_interval = dict()
    start_time = dict()
    
    for _, row in schools_students_attend.iterrows():
        dropoff_dict[row['tt_ind']] = row['dropoff_time']
        dropoff_interval[row['tt_ind']] = row['bell_time_intervals']
        start_time[row['tt_ind']] = row['start_time']
        
    constants.DROPOFF_TIME = dropoff_dict 
    constants.BELL_TIMES = start_time
    constants.DROPOFF_RANGE = dropoff_interval

# Set up up the dataframes to make stops, zipdata, schools, and phonebook
# Filter and wrangle through data 
def setup_data(stops, zipdata, schools, phonebook, bell_times):
    
    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/'

    stops = prefix+'stop_geocodes_fixed.csv'
    zipdata =prefix+'zipData.csv'
    schools = prefix+'school_geocodes_fixed.csv'
    phonebook = prefix+'totalPhoneBook.csv'
    bell_times = prefix+'bell_times.csv'

    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    bell_times = pd.read_csv(bell_times, low_memory=False, encoding='windows-1252')
    schools = pd.read_csv(schools, dtype={'Location_Code': int, 'School_Name': str, 'Cost_Center': int, 'Lat': float, 'Long': float}, low_memory=False)
    schools = schools[['Location_Code', 'School_Name', 'Cost_Center', 'Lat', 'Long']]
    schools = pd.merge(schools, bell_times[['start_time','bell_time_intervals', 'dropoff_time', 'Cost_Center']], on ='Cost_Center', how='left')
    
    school_index_list = list()
    for row in schools.iterrows():
        school_index_list.append(constants.CODES_INDS_MAP[constants.SCHOOLS_CODES_MAP[str(row[1]['Cost_Center'])]])

    schools['tt_ind'] = school_index_list
    schools = edit_bell_times(schools)
    
    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Prog': str, 'Mod_Grade': int, 'Cost_Center': str, "AM_Trip": str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Prog', 'Cost_Center', 'Cost_Center_Name','Mod_Grade','AM_Stop_Address', 'AM_Route', 'AM_Trip']]
    phonebook = phonebook[phonebook['AM_Route'] != str(9500)]
    phonebook = phonebook[phonebook['AM_Trip'] == str(1)]
    phonebook = phonebook[phonebook['AM_Stop_Address'] != str(", , ")]
    phonebook = pd.merge(phonebook, stops[['AM_Stop_Address','Lat', 'Long']], on= 'AM_Stop_Address', how='inner')
    phonebook = phonebook.dropna()     # 36145 -> 36143
    phonebook['Cost_Center']=phonebook['Cost_Center'].astype(int)

    phonebook["School_type"] = None
    mask = (phonebook['Mod_Grade'] < 6)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "elem")
    mask = (phonebook['Mod_Grade'] >= 6) & (phonebook['Mod_Grade'] < 9)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "middle")
    mask = (phonebook['Mod_Grade'] >= 9) & (phonebook['Mod_Grade'] <=13)
    phonebook['School_type'] = phonebook['School_type'].mask(mask, "high")
    
    phonebook.loc[phonebook['School_type'] == 'elem', 'School_type'] = 0
    phonebook.loc[phonebook['School_type'] == 'middle', 'School_type'] = 1
    phonebook.loc[phonebook['School_type'] == 'high', 'School_type'] = 2
    phonebook = phonebook[phonebook.Prog.isin(constants.PROG_TYPES)]
    phonebook = phonebook.rename(index=str, columns={"Lat": "Lat", "Long": "Long"})

    schools_students_attend = phonebook["Cost_Center"].drop_duplicates().dropna()
    schools_students_attend = schools.loc[schools['Cost_Center'].isin(schools_students_attend)]
    schools_students_attend = pd.merge(schools_students_attend, phonebook[['Cost_Center', 'School_type']], on=['Cost_Center'], how='inner')
    schools_students_attend = schools_students_attend.drop_duplicates(subset="Cost_Center")
    phonebook = pd.merge(phonebook, schools_students_attend[['Cost_Center', 'tt_ind']], on=['Cost_Center'], how='inner')
    schools_students_attend = schools_students_attend.drop_duplicates(subset="tt_ind")
    schools_students_attend = schools_students_attend.reset_index(drop=True)

    # Cluster schools and merge back into list of schools_students_attend
    clustered_schools = obtainClust_DBSCAN_AGGO_combined(schools_students_attend)
    
    # Check requirements 
    clustered_schools['early_start_time'] = clustered_schools['start_time_seconds'] - clustered_schools['bell_time_intervals']
    clustered_schools = solve_school_constraints(clustered_schools)   
 
    schools_students_attend = pd.merge(schools_students_attend, clustered_schools[['label', 'tt_ind']], on=['tt_ind'], how='inner').drop_duplicates()
    schools_students_attend = schools_students_attend.sort_values(['label'], ascending=[True])
    update_school_dropoff_info(schools_students_attend)

    schoolcluster_students_map_df = partition_students(schools_students_attend, phonebook)
    update_verif_counters(schoolcluster_students_map_df)
    return_clustered_schools = setup_clusters(schools_students_attend, schoolcluster_students_map_df)
    return return_clustered_schools

# Setup clusters: input all required files 
def setup_clusters(cluster_schools_df, schoolcluster_students_df):
    clustered_schools = defaultdict(int)
    for idx in range(0, max(cluster_schools_df['label'])):
        clustered_schools[idx] = Cluster(cluster_schools_df[cluster_schools_df['label'] == idx], schoolcluster_students_df[idx])
    return clustered_schools

# Setup the buses
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

    # Setup contract buses
    contract_cap_counts = setup_contract_buses(cap_counts_list)
    return defaultdict(int, cap_counts_list), defaultdict(int, contract_cap_counts)

# Setup contract buses
def setup_contract_buses(cap_counts_list):
    contract_cap_counts = copy.deepcopy(cap_counts_list)
    for i in range(0, len(contract_cap_counts)):
        contract_cap_counts[i][1] = 0 
    return contract_cap_counts

# Set up the school_type map 
def setup_schooltype_map(schools_students_attend):
    schooltype_map = dict()
    for index, row in schools_students_attend.iterrows():
        schooltype_map[row['tt_ind']] = row['School_type']
    return schooltype_map
 