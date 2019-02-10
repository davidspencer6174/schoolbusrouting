import pandas as pd, numpy as np
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
import csv 
from collections import Counter
import math
from random import randint

verbose = 1
stop_point = 10


# Setup
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

    phonebook = phonebook.rename(index=str, columns={"Lat": "stop_Lat", "Long": "stop_Long"})
    
    return depot, stops, zipdata, schools, phonebook

# Peform the clustering using KMEANS
# stops: Lat, long values
# n_clusters: number of clusters
def obtainClust_KMEANS(stops, n_clusters):
    kmeans = KMeans(n_clusters, random_state=0).fit(stops)
    stops['label'] = kmeans.labels_
    return stops

# Estimate cluster params for KMEANS 
def estimateClusParamsKMEANS(subset):
    # RANDOMLY picks bus to use to transport
    # Find better way to choose bus sizes instead of randomly picking
    # bus_size = random.choice(list(bus_dict.keys()))

#    ans = sil_coeff = 0 
#    for n_cluster in range(2, len(subset)):
#        kmeans = KMeans(n_clusters=n_cluster).fit(subset)
#        label = kmeans.labels_
#        sil_coeff = silhouette_score(subset, label, metric='euclidean')
#        
#        if verbose:
#            print("For n_clusters={}, The Silhouette Coefficient is {}".format(n_cluster, sil_coeff))
#
#        if sil_coeff > ans:
#            ans = sil_coeff
#            n = n_cluster
#    
    n = randint(3, len(subset))
    if verbose:
        print(" ------ ")
            
    return n

# Cluster based on schools 
def schoolBasedClustering(phonebook):
    result_schools = pd.DataFrame(phonebook["Cost_Center"].drop_duplicates())
    result_schools["clusteredStops"] = None
    count = 0 
    
    for index, row in result_schools.iterrows():
        s = row["Cost_Center"]
        total_students = phonebook[(phonebook.Cost_Center == s)][["stop_Lat","stop_Long"]]
        print(index)
        if index >= str(103):
            break
        
        subset = phonebook[(phonebook.Cost_Center == s)][["stop_Lat","stop_Long"]].drop_duplicates()
        subset = subset.dropna()
        
        if verbose:
            print(s)

        if len(subset) > 3:
            n = estimateClusParamsKMEANS(subset)
            clustered = obtainClust_KMEANS(subset, n)
            result_schools.at[index, 'clusteredStops']= clustered.values
        else:
            result_schools.at[index, 'clusteredStops']= subset.values

        count += 1 
        if count == stop_point:
            break
    return result_schools

# Output results of one cluster
def outputResults(clustered, i):
    clustered = clustered.sort_values(by='label')
    print(clustered)
    file = open(str(i) + "output" + ".txt", "w") 
    file.write("category,latitude,longitude\n") 

    for index, row in clustered.iterrows():
        print(str(int(row["label"])) + "," + str(row["Lat"]) + "," + str(row["Long"]) + "\n")
        file.write(str(int(row["label"])) + "," + str(row["Lat"]) + "," + str(row["Long"]) + "\n") 
    file.close()

# Write to file -- results of all clusters
def toFile(clusters):
    count = 0 
    for i in range(0, len(clusters)):
        temp = pd.DataFrame(clusters["clusteredStops"][i], columns=['Lat','Long','label'])
        outputResults(temp, i)
        count += 1

        if count == stop_point: 
            break

def clusterBasedOnSplit(phonebook, schools, stops):
    
    levels = ['Elem', 'Middle', 'High']
    data = pd.DataFrame(columns=['Level','School_Clustered','Stops_Clustered'])
    data['Level'] = levels
    
    for index, row in data.iterrows(): 
        l = row['Level']
        
        schoollevels = phonebook.loc[phonebook['Level'] == l]
        temp1 = schools[schools['Cost_Center'].isin(schoollevels['Cost_Center'])]
        temp2 = stops[stops['AM_Stop_Address'].isin(schoollevels['AM_Stop_Address'])]
        
        temp1 = temp1[['Lat','Long']]
        temp2 = temp2[['Lat','Long']]
                        
        n1 = 20
        n2 = 50 
        
#        n1 = estimateClusParamsKMEANS(temp1)
#        n2 = estimateClusParamsKMEANS(temp2)

        clusteredschool = obtainClust_KMEANS(temp1, n1)
        clusteredstops = obtainClust_KMEANS(temp2, n2)
        
        data.at[index, 'School_Clustered']= clusteredschool.values
        data.at[index, 'Stops_Clustered']= clusteredstops.values

    return data


# Main
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
depot, stops, zipdata, schools, phonebook = setup_data(prefix+'depot_geocodes.csv', 
                                                       prefix+'stop_geocodes_fixed.csv', prefix+'zipData.csv', 
                                                       prefix+'school_geocodes_fixed.csv', prefix+'totalPhoneBook.csv')

clustered_by_levels = clusterBasedOnSplit(phonebook, schools, stops)





