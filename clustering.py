import pandas as pd 
import numpy as np 
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from collections import Counter
import constants

# Reformat the outputs from DBSCAN
def reformatCluster_DBSCAN(clusters):
    df = pd.DataFrame()
    for i in range(0, len(clusters)):
        temp = pd.DataFrame(np.array(clusters[i]), columns = ['Lat','Long'])
        temp['label'] = i
        df = df.append(pd.DataFrame(temp, columns=['Lat','Long','label']),ignore_index=True)
    return df 

# Obtain the modified subset of the total travel times
# This is used to perform clustering
def obtain_sub_travel_times(new_df):
    
    temp_df = new_df.sort_values(by=['School_type'])
    indexes = list(temp_df['tt_ind'])
    sub_travel_times = constants.DF_TRAVEL_TIMES.iloc[indexes,:]
    sub_travel_times = sub_travel_times.iloc[:,indexes]

    mid_start_index = temp_df["School_type"].searchsorted(1)
    high_start_index = temp_df["School_type"].searchsorted(2)
    
    sub_travel_times.iloc[0:mid_start_index,high_start_index:] = 9999999999
    sub_travel_times.iloc[high_start_index:,0:mid_start_index] = 9999999999

    return sub_travel_times 

# DBSCAN using custom distance 
def obtainClust_DBSCAN_custom(schools_students_attend):
    
    schools_students_attend = schools_students_attend.drop_duplicates()
    loc_codes = list(dict.fromkeys(schools_students_attend["tt_ind"].drop_duplicates().tolist()))
    new_df = pd.DataFrame()
    
    # School serving multiple levels, we pick middle 
    for ind in loc_codes:
        temp_group = schools_students_attend[schools_students_attend['tt_ind'] == ind]
        school_type_temp = set(temp_group['School_type'])
        
        if len(school_type_temp) == 1: 
            new_df = new_df.append(temp_group)
        
        # if there is middle, pick middle
        elif 'middle' in school_type_temp: 
            new_df = new_df.append(temp_group[temp_group['School_type'] == 'middle'])
          
        # If elem and high, we just pick high 
        else: 
            new_df = new_df.append(temp_group[temp_group['School_type'] == 'high'])
    
    new_df = new_df.drop_duplicates('tt_ind')
    
    new_df.loc[new_df['School_type'] == 'elem', 'School_type'] = 0
    new_df.loc[new_df['School_type'] == 'middle', 'School_type'] = 1
    new_df.loc[new_df['School_type'] == 'high', 'School_type'] = 2

    test_df = new_df[:250]

    # Create subset of travel times and modify distances 
    sub_travel_times = obtain_sub_travel_times(test_df)
    
    # Perform clustering
    db = DBSCAN(eps=constants.RADIUS, min_samples=constants.MIN_SAMPLES).fit(sub_travel_times)
    sub_tt_ind = list(sub_travel_times.columns.values)
        
    test_df['tt_ind_cat'] = pd.Categorical(test_df['tt_ind'], categories=sub_tt_ind, ordered=True)
    test_df = test_df.sort_values('tt_ind_cat')
    clustered_schools = test_df.assign(label = db.labels_)
    output_geo_with_labels(clustered_schools)
    
    return clustered_schools

# Use DBSCAN to perform clustering
def obtainClust_DBSCAN(loc, dist, min_samples):
    coordinates = loc[['Lat', 'Long']].values
    kms_per_radian = 6371.0088
    epsilon = dist / kms_per_radian 
    db = DBSCAN(eps=epsilon, min_samples=min_samples, 
                algorithm='ball_tree', metric='haversine').fit(np.radians(coordinates))
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))
    clusters = pd.Series([coordinates[cluster_labels == n] for n in range(num_clusters)])
    return reformatCluster_DBSCAN(clusters)

# Use KMeans to perform clustering
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

# Break relateively large clusters and use Kmeans to break
def break_large_clusters(data, break_num, limit):
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
def partition_students(clustered_schools, phonebook):
    counts = Counter(clustered_schools['label'])
    schoolcluster_students_map = dict()
     
    for row in counts.items():
        
        temp = clustered_schools.loc[clustered_schools['label'] == row[0]].copy()  
        schools_in_cluster = list(temp['Cost_Center'].astype(str))
        students = phonebook[phonebook['Cost_Center'].isin(schools_in_cluster)].copy()
        students.loc[:,'School_Group'] = row[0]
        
        student_labels = obtainClust_KMEANS(students, constants.BREAK_NUM)
        students = pd.merge(students, student_labels, on=['Lat', 'Long'], how='inner').drop_duplicates()
        students = students.sort_values(by=['label'])
        
        schoolcluster_students_map[row[0]] = students
    return schoolcluster_students_map

