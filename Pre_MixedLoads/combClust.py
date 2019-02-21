import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from collections import Counter
import pickle

verbose = 0
break_num = 6

def setup_data(depotfile, stops, zipdata, schools, phonebook):
    depot = pd.read_csv(depotfile, low_memory=False)
    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    schools = pd.read_csv(schools, dtype={'Location_Code': int, 'Cost_Center': int, 'Lat': float, 'Long': float}, low_memory=False)
    cols = range(2,6)
    schools.drop(schools.columns[cols],axis=1,inplace=True)
    
    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Cost_Center': str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Cost_Center', 'Cost_Center_Name','Grade','AM_Stop_Address', 'AM_Route']]
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
    phonebook['Level'] = phonebook['Level'].mask(mask, "Elem")
    mask = (phonebook['Grade'] >= 6) & (phonebook['Grade'] < 9)
    phonebook['Level'] = phonebook['Level'].mask(mask, "Middle")
    mask = (phonebook['Grade'] >= 9) & (phonebook['Grade'] <=13)
    phonebook['Level'] = phonebook['Level'].mask(mask, "High")

    phonebook = phonebook.rename(index=str, columns={"Lat": "Lat", "Long": "Long"})
    return depot, stops, zipdata, schools, phonebook

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

def outputDataframe(clustered):
    clustered = clustered.sort_values(by='label')
    file = open("temp" + ".txt", "w") 
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
        
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
depot, stops, zipdata, schools, phonebook = setup_data(prefix+'depot_geocodes.csv', 
                                                       prefix+'stop_geocodes_fixed.csv', prefix+'zipData.csv', 
                                                       prefix+'school_geocodes_fixed.csv', prefix+'totalPhoneBook.csv')

phonebook = phonebook.loc[phonebook['Level'] == "Elem"]
elemschools = phonebook["Cost_Center"].drop_duplicates()
elemschools = schools.loc[schools['Cost_Center'].isin(elemschools)]

total = obtainClust_DBSCAN(elemschools, 1.9, 1)
elemschool_clusters = breakLargeClusters(total, 4, 5)
elemschool_clusters = breakLargeClusters(elemschool_clusters, 2, 3)

elemschools = pd.merge(elemschools, elemschool_clusters, on=['Lat', 'Long'], how='inner').drop_duplicates()
elemschools = elemschools.sort_values(by=['label'])

schoolcluster_students_map = partitionStudents(elemschools, phonebook)


# Testing
subset = elemschools.loc[elemschools['label'] == 0].copy()  
outputDataframe(subset)

# Write to file
elemschools.to_csv('elem_clustered_schools_file', sep='\t', encoding='utf-8')

# Write dictionary
with open('codes_inds_map' ,'wb') as handle:
    pickle.dump(codes_inds_map, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('clusteredschools_students_map' ,'wb') as handle:
    pickle.dump(schoolcluster_students_map, handle, protocol=pickle.HIGHEST_PROTOCOL)

# Read dictionary
with open('SC_stops_file' ,'rb') as handle:
    schoolcluster_students_map = pickle.load(handle)






# TESTING 
labels = []

for i in range(0, len(temp)):
    labels.append(i)

temp['label'] = labels
outputDataframe(temp)








