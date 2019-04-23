import pandas as pd 
import numpy as np 
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering 
from collections import Counter
import constants
import copy 

# Reformat the outputs from DBSCAN
def reformatCluster_DBSCAN(clusters):
    df = pd.DataFrame()
    for i in range(0, len(clusters)):
        temp = pd.DataFrame(np.array(clusters[i]), columns = ['Lat','Long'])
        temp['label'] = i
        df = df.append(pd.DataFrame(temp, columns=['Lat','Long','label']),ignore_index=True)
    return df 

# Obtain the modified subset of the total travel times
# This is used to perform clustering:
def obtain_sub_travel_times(new_df, isolate_option):
    
    temp_df = new_df.sort_values(by=['School_type'])
    indexes = list(temp_df['tt_ind'])
    sub_travel_times = constants.DF_TRAVEL_TIMES.iloc[indexes,:]
    sub_travel_times = sub_travel_times.iloc[:,indexes]

    mid_start_index = temp_df["School_type"].searchsorted(1)
    high_start_index = temp_df["School_type"].searchsorted(2)
        
    if isolate_option == 'None':
        pass
    
    # Isolate elementary schools
    elif isolate_option == 'elem':
        sub_travel_times.iloc[mid_start_index:, 0:mid_start_index] = 99999999
        sub_travel_times.iloc[0:mid_start_index, mid_start_index:] = 99999999
        
    # Isolate high schools
    elif isolate_option == 'high':
        sub_travel_times.iloc[high_start_index:,0:high_start_index] = 99999999
        sub_travel_times.iloc[0:high_start_index, high_start_index:] = 99999999
        
    elif isolate_option == 'remove_elem_high':
        sub_travel_times.iloc[high_start_index:, 0:mid_start_index] = 99999999
        sub_travel_times.iloc[0:mid_start_index, high_start_index:] = 99999999
        
    return sub_travel_times 

# DBSCAN using custom distance 
def obtainClust_DBSCAN_AGGO_combined(schools_students_attend):
    
    schools_students_attend = schools_students_attend.drop_duplicates()
    loc_codes = list(dict.fromkeys(schools_students_attend["tt_ind"].drop_duplicates().tolist()))
    original_df = pd.DataFrame()
    
    # School serving multiple levels, we pick middle 
    for ind in loc_codes:
        temp_group = schools_students_attend[schools_students_attend['tt_ind'] == ind]
        school_type_temp = set(temp_group['School_type'])
        
        if len(school_type_temp) == 1: 
            original_df = original_df.append(temp_group)
        
        # if there is middle, pick middle
        elif 1 in school_type_temp: 
            original_df = original_df.append(temp_group[temp_group['School_type'] == 1])
          
        # If elem and high, we just pick high 
        else: 
            original_df = original_df.append(temp_group[temp_group['School_type'] == 2])
    
    # Drop duplicates of original df 
    original_df = original_df.drop_duplicates('tt_ind')
    
    clus_DBSCAN_df = original_df

    # Use DBSCAN to estimate the number of clusters 
    sub_travel_times = obtain_sub_travel_times(clus_DBSCAN_df, 'None')
    db = DBSCAN(eps=constants.RADIUS, min_samples=constants.MIN_SAMPLES).fit(sub_travel_times)
    tt_ind = list(sub_travel_times.columns.values)
    clus_DBSCAN_df = clus_DBSCAN_df.assign(tt_ind_cat=pd.Categorical(clus_DBSCAN_df['tt_ind'], categories=tt_ind, ordered=True))
    clus_DBSCAN_df = clus_DBSCAN_df.sort_values('tt_ind_cat')
    clus_DBSCAN_df = clus_DBSCAN_df.assign(label = db.labels_)
    
    # Use agglo to perform clustering
    agglo_sub_travel_times = obtain_sub_travel_times(original_df, 'remove_elem_high')
    agglo_sub_travel_times = np.maximum(agglo_sub_travel_times, agglo_sub_travel_times.transpose())
    
    # Copy original df into final df based on agglo clustering 
    final_agglo_df = original_df

    # find number of clusters using agglo clustering
    num_clusters_agglo = find_num_clusters_aggo(clus_DBSCAN_df, agglo_sub_travel_times) 

    # push back agglo clustering labels into df
    model = AgglomerativeClustering(affinity='precomputed', n_clusters=num_clusters_agglo, linkage='average').fit(agglo_sub_travel_times)
    sub_tt_ind = list(agglo_sub_travel_times.columns.values)
    final_agglo_df = final_agglo_df.assign(tt_ind_cat=pd.Categorical(final_agglo_df['tt_ind'], categories=sub_tt_ind, ordered=True))
    final_agglo_df = final_agglo_df.sort_values('tt_ind_cat')
    final_agglo_df = final_agglo_df.assign(label = model.labels_)

    return final_agglo_df


# find the appropriate number of clusters to be used in agglomerative clustering
def find_num_clusters_aggo(clus_DBSCAN_df, travel_times):
    
    num_clus_DBSCAN = max(clus_DBSCAN_df['label'])
    agglo_df = copy.deepcopy(clus_DBSCAN_df.drop(['label'], axis = 1))
    
    # Iterate down 
    for num_clus in range(num_clus_DBSCAN-10, num_clus_DBSCAN-20, -1):
        model = AgglomerativeClustering(affinity='precomputed', n_clusters=num_clus, linkage='average').fit(travel_times)
        agglo_tt_ind = list(travel_times.columns.values)
        agglo_df = agglo_df.assign(tt_ind_cat=pd.Categorical(agglo_df['tt_ind'], categories=agglo_tt_ind, ordered=True))
        agglo_df = agglo_df.sort_values('tt_ind_cat')
        agglo_df = agglo_df.assign(label = model.labels_)
        
        total_tt = np.zeros((len(travel_times), len(travel_times)))

        # Make the new travel time index 
        count = 0 
        for i in range(0, max(agglo_df['label'])):
            subset_agglo_df = agglo_df[agglo_df['label'] == i]
            subset_travel_time = obtain_sub_travel_times(subset_agglo_df, 'remove_elem_high')
            total_tt[count:count+len(subset_travel_time), count:count+len(subset_travel_time)] = subset_travel_time
            count += len(subset_travel_time)
    
        dist_within_clust = [round(sum(total_tt[i]),2) for i in range(0, len(total_tt))]
        dist_within_clust = list(filter(lambda a: a!=0, dist_within_clust))
        
        if max(dist_within_clust) > constants.RADIUS:
            return num_clus+1
        
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
def partition_students(schools_students_attend, phonebook):
    
    counts = Counter(schools_students_attend['label'])
    schoolcluster_students_map = dict()
     
    for row in counts.items():

        temp = schools_students_attend.loc[schools_students_attend['label'] == row[0]].copy()  
        schools_in_cluster = list(temp['Cost_Center'].astype(str))
        students = phonebook[phonebook['Cost_Center'].isin(schools_in_cluster)].copy()
        students.loc[:,'School_Group'] = row[0]
        
#        students.loc[:,'tt_ind'] = round(students['Lat'],6).astype(str) + ";" + round(students['Long'],6).astype(str)
#        students = students.replace({"tt_ind": constants.CODES_INDS_MAP})
#        students['tt_ind'].astype(np.int64)
#        
#        clustered_stops = obtainClust_DBSCAN_custom(students)
#        students = pd.merge(students, clustered_stops[['label', 'tt_ind']], on=['tt_ind'], how='inner').drop_duplicates()
#        students = students.sort_values(['label'], ascending=[True])
        
        student_labels = obtainClust_KMEANS(students, constants.BREAK_NUM)
        students = pd.merge(students, student_labels, on=['Lat', 'Long'], how='inner').drop_duplicates()
        students = students.sort_values(by=['label'])
        schoolcluster_students_map[row[0]] = students
        
    return schoolcluster_students_map

