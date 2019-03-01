import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from collections import Counter
import pickle

verbose = 0
break_num = 6

def setup_data(stops, zipdata, schools, phonebook, bell_times, schools_codes_mapFile, codes_inds_mapFile):
    
    with open(schools_codes_mapFile,'rb') as handle:
        schools_codes_map = pickle.load(handle)
    with open(codes_inds_mapFile ,'rb') as handle:
        codes_inds_map = pickle.load(handle)

    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    bell_times = pd.read_csv(bell_times, low_memory=False, encoding='windows-1252')
    schools = pd.read_csv(schools, dtype={'Location_Code': int, 'School_Name': str, 'Cost_Center': int, 'Lat': float, 'Long': float}, low_memory=False)
    schools = schools[['Location_Code', 'School_Name', 'Cost_Center', 'Lat', 'Long']]
    schools = pd.merge(schools, bell_times[['r1_start','Cost_Center']], on ='Cost_Center', how='left')
    
    school_index_list = list()
    for ind, row in schools.iterrows():
        school_index_list.append(codes_inds_map[schools_codes_map[str(row['Cost_Center'])]])
    schools['tt_ind'] = school_index_list
    schools = editBellTimes(schools)

    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Prog': str, 'Cost_Center': str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Prog', 'Cost_Center', 'Cost_Center_Name','Grade','AM_Stop_Address', 'AM_Route']]
    phonebook = phonebook[phonebook['AM_Route'] != str(9500)]
    phonebook = phonebook.dropna()
    phonebook = phonebook[phonebook['AM_Stop_Address'] != str(", , ")]
    phonebook = phonebook.dropna()
    phonebook =  pd.merge(phonebook,
                 stops[['AM_Stop_Address','Lat', 'Long']],
                 on= 'AM_Stop_Address',
                 how='left')
    
    phonebook["Level"] = None
    mask = (phonebook['Grade'] < 6)
    phonebook['Level'] = phonebook['Level'].mask(mask, "elem")
    mask = (phonebook['Grade'] >= 6) & (phonebook['Grade'] < 9)
    phonebook['Level'] = phonebook['Level'].mask(mask, "middle")
    mask = (phonebook['Grade'] >= 9) & (phonebook['Grade'] <=13)
    phonebook['Level'] = phonebook['Level'].mask(mask, "high")

    phonebook = phonebook.rename(index=str, columns={"Lat": "Lat", "Long": "Long"})
    return stops, zipdata, schools, phonebook 

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

def reformatClustersDBSCAN(clusters):
    df = pd.DataFrame()
    for i in range(0, len(clusters)):
        temp = pd.DataFrame(np.array(clusters[i]), columns = ['Lat','Long'])
        temp['label'] = i
        df = df.append(pd.DataFrame(temp, columns=['Lat','Long','label']),ignore_index=True)
    return df 

def obtainClust_DBSCAN(loc, dist, min_samples):
    coordinates = loc[['Lat', 'Long']].values
    kms_per_radian = 6371.0088
    epsilon = dist / kms_per_radian 
    db = DBSCAN(eps=epsilon, min_samples=min_samples, 
                algorithm='ball_tree', metric='haversine').fit(np.radians(coordinates))
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    clusters = pd.Series([coordinates[cluster_labels == n] for n in range(num_clusters)])
    
    if verbose:
        print('Number of clusters: {}'.format(num_clusters))
    return reformatClustersDBSCAN(clusters)

def obtainClust_KMEANS(loc, base_number):
    loc = loc[['Lat','Long']].drop_duplicates().dropna()
    loc = loc[['Lat', 'Long']].values
    n_clusters = int(len(loc)/base_number)
    
    if n_clusters == 0:
        n_clusters = 1
    
    kmeans = KMeans(n_clusters, random_state=0).fit(loc)
    loc = pd.DataFrame(loc, columns=['Lat','Long'])
    loc['label'] = kmeans.labels_
    return loc

def outputGeolocationsWithLabels(clustered):
    clustered = clustered.sort_values(by='label')
    file = open("elem_schools_geo" + ".txt", "w") 
    file.write("category,latitude,longitude\n") 
    
    for index, row in clustered.iterrows():
#        print(str(int(row["label"])) + "," + str(row["Lat"]) + "," + str(row["Long"]) + "\n")
        file.write(str(int(row["label"])) + "," + str(row["Lat"]) + "," + str(row["Long"]) + "\n") 
    file.close()

# Break relateively large clusters and use Kmeans to break
def breakLargeClusters(data, break_num, limit):
    counts = Counter(data['label'])
    result = pd.DataFrame(np.random.randint(low=0, high=1, size=(1, 3)), columns=['Lat','Long','label'])    
    for row in counts.items():
        temp = data.loc[data['label'] == row[0]].copy()  
        if row[1] > limit: 
            broken = obtainClust_KMEANS(temp, break_num)
            broken['label'] = broken['label'] + max(result['label'])
            result = result.append(broken)
        else:
            temp['label'] = temp['label'] + max(result['label'])
            result = result.append(temp)
    result = result.iloc[1:]
    result = result.sort_values(by=['label'])
    return result

# Partition students based on the school clusters
def partitionStudents(schools, phonebook):
    counts = Counter(schools['label'])
    schoolcluster_students_map = dict()
    
    for row in counts.items():
        temp = schools.loc[schools['label'] == row[0]].copy()  
        schools_in_cluster = list(temp['Cost_Center'].astype(str))
        students = phonebook[phonebook['Cost_Center'].isin(schools_in_cluster)].copy()
        students.loc[:,'School_Group'] = row[0]
        
        student_labels = obtainClust_KMEANS(students, break_num)
        students = pd.merge(students, student_labels, on=['Lat', 'Long'], how='inner').drop_duplicates()
        students = students.sort_values(by=['label'])
        
        schoolcluster_students_map[row[0]] = students
    return schoolcluster_students_map

# Write dictionaries to disc
# new_schools: dataframe of clustered schools
# schoolcluster_students_map_df: 
def outputDictionary(schools_students_attend, schoolcluster_students_map_df, student_level):
    schools_students_attend.to_csv(str(student_level) + '_clustered_schools_file.csv', sep=';', encoding='utf-8')
    with open(str(student_level) + '_clusteredschools_students_map' ,'wb') as handle:
        pickle.dump(schoolcluster_students_map_df, handle, protocol=pickle.HIGHEST_PROTOCOL)

##############################################################################################################################
# MAIN
##############################################################################################################################
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
stops, zipdata, schools, phonebook = setup_data(prefix+'stop_geocodes_fixed.csv', 
                                                prefix+'zipData.csv', 
                                                prefix+'school_geocodes_fixed.csv', 
                                                prefix+'totalPhoneBook.csv',
                                                prefix+'bell_times.csv',
                                                prefix+'/mixed_load_data/schools_codes_map',
                                                prefix+'/mixed_load_data/codes_inds_map')

School_Level = "middle"
prog_types = ['P', 'X', 'M']
phonebook = phonebook.loc[phonebook['Level'] == School_Level]
phonebook = phonebook[phonebook.Prog.isin(prog_types)]

schools_students_attend = phonebook["Cost_Center"].drop_duplicates()
schools_students_attend = schools.loc[schools['Cost_Center'].isin(schools_students_attend)]
clustered_schools = obtainClust_DBSCAN(schools_students_attend, 2, 1)

#elemschool_clusters = breakLargeClusters(total, 4, 5)

schools_students_attend = pd.merge(schools_students_attend, clustered_schools, on=['Lat', 'Long'], how='inner').drop_duplicates()
schools_students_attend = schools_students_attend.sort_values(['label', 'r1_start'], ascending=[True, False])

schoolcluster_students_map_df = partitionStudents(schools_students_attend, phonebook)

print(Counter(clustered_schools['label']))
print("Num of clusters: " + str(len(Counter(clustered_schools['label']))))

# outputDictionary(schools_students_attend, schoolcluster_students_map_df, School_Level)

##############################################################################################################################
# MISC
##############################################################################################################################
subset = schools_students_attend.loc[schools_students_attend['label'] == 0].copy() 
test_1 = schoolcluster_students_map_df[0].loc[schoolcluster_students_map_df[0]['label'] ==0].copy()
 
outputGeolocationsWithLabels(subset)

test = schoolcluster_students_map_df[0]
stops_subset = test.loc[test['label'] == 0]
stops_subset = stops_subset[['Lat','Long','label','AM_Stop_Address']].drop_duplicates().dropna()






