import pandas as pd, numpy as np
from sklearn.cluster import DBSCAN
afrom sklearn.metrics import silhouette_score
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
import csv 
from collections import Counter
import math
import random
from random import randint

stop_point = 20
verbose = 1

# Setup
def setup_data(depotfile, stops, zipdata, schools, phonebook, bus_cap):
    
    depot = pd.read_csv(depotfile, low_memory=False)
    stops = pd.read_csv(stops, low_memory=False)
    zipdata = pd.read_csv(zipdata, low_memory=False)
    
    schools = pd.read_csv(schools, low_memory=False)
    cols = range(2,6)
    schools.drop(schools.columns[cols],axis=1,inplace=True)
    
    phonebook = pd.read_csv(phonebook, dtype={"RecordID": str, 'Cost_Center': str, "AM_Route": str}, low_memory=False)
    phonebook = phonebook[['RecordID', 'Cost_Center', 'AM_Stop_Address', 'AM_Route']]
    phonebook = phonebook[phonebook['AM_Route'] != str(9500)]
    phonebook = phonebook.dropna()
    phonebook = phonebook[phonebook['AM_Stop_Address'] != str(", , ")]
    phonebook = phonebook.dropna()
    phonebook =  pd.merge(phonebook,
                 stops[['AM_Stop_Address','Lat', 'Long']],
                 on= 'AM_Stop_Address',
                 how='left')
    
    phonebook = phonebook.rename(index=str, columns={"Lat": "stop_Lat", "Long": "stop_Long"})

    bus_cap = pd.read_csv(bus_cap, low_memory=False)
    bus_dict = dict(Counter(bus_cap["Cap"]))
    return depot, stops, zipdata, schools, phonebook, bus_dict

# Cluster output from DBSCAN is funky
# Print out the number of stops within each cluster and returns total of stops
def printClusterSize(clusters):
    total = 0
    for i in range(0, len(clusters)):
        print(len(clusters[i]))
        total += len(clusters[i])
    print("Total Size: " + str(total))
    return total
    
# Cluster output from DBSCAN is funky
# This function reformats the output into a DF with [Lat, Long, label]
def reformatClustersDBSCAN(clusters):
    df = pd.DataFrame()
    for i in range(0, len(clusters)):
        temp = pd.DataFrame(np.array(clusters[i]), columns = ['Lat','Long'])
        temp['label'] = i
        df = df.append(pd.DataFrame(temp, columns=['Lat','Long','label']),ignore_index=True)
    return df 

# Get the centermost point in a cluster
def get_centermost_point(cluster):
    centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
    centermost_point = min(cluster, key=lambda point: great_circle(point, centroid).m)
    return tuple(centermost_point)

# Return stops that did not get clustered
# stops: original stops 
# newClusters: stops that got clustered 
def getUnclustered(newClusters, stops):
    test = stops[['Lat', 'Long']]
    newTest = newClusters[['Lat', 'Long']]
    x = pd.concat([test, newTest])
    unclustered = x.drop_duplicates(keep=False, inplace=False)
    return unclustered

# Peform the clustering using DBSCAN
# stops: Lat, long values
# dist: max. distance between points to be considered a cluster
# minSamples: 
def obtainClust_DBSCAN(stops, dist, min_samples):
    coordinates = stops[['Lat', 'Long']].values
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

# Estimate cluster params for DBSCAN
def estimateClusParamsDBSCAN(subset, zipinfo):
    # TEMP FIX: split each zipcode into 5 distinct parts
    # Find better way to choose bus sizes instead of using constant
    minsamples = int(zipinfo['studentCount'] / 5)
    dist = math.ceil(zipinfo['area'] / 5)
    return dist, minsamples

# Peform the clustering using KMEANS
# stops: Lat, long values
# n_clusters: number of clusters
def obtainClust_KMEANS(stops, n_clusters):
    kmeans = KMeans(n_clusters, random_state=0).fit(stops)
    stops['label'] = kmeans.labels_
    return stops

# Estimate cluster params for KMEANS 
def estimateClusParamsKMEANS(subset, bus_dict):
    # RANDOMLY picks bus to use to transport
    # Find better way to choose bus sizes instead of randomly picking
    # bus_size = random.choice(list(bus_dict.keys()))
#    n = randint(1, int(len(subset)/2))
    
    ans = sil_coeff = 0 
    for n_cluster in range(2, len(subset)):
        kmeans = KMeans(n_clusters=n_cluster).fit(subset)
        label = kmeans.labels_
        sil_coeff = silhouette_score(subset, label, metric='euclidean')
        
        if verbose:
            print("For n_clusters={}, The Silhouette Coefficient is {}".format(n_cluster, sil_coeff))

        if sil_coeff > ans:
            ans = sil_coeff
            n = n_cluster
            
    if verbose:
        print(" ------ ")

    return n

# Append newcluster to total results, preserve labels
def appendClusters(results, clustered):
    if len(results) == 0:
        results = clustered     
    else:
        buff = results['label'].max() + 1
        clustered['label'] = clustered['label'] + buff 
        results = results.append(clustered)
    return results 

# Perform clustering based on each zip 
# We will use informatino regarding zip-code area, population density, etc.
# Cluster each zip to 'n' clusters
def zipBasedClustering(stops, zipdata, bus_dict, algType):
    
    results_zips = pd.DataFrame(stops['Zip'].drop_duplicates())
    results_zips["label"] = None

    for index, row in results_zips.iterrows():
        break
        z = row["Zip"]
        count = 0 

        # Obtain subset of stops and information regarding particular zipcode
        subset = (stops.loc[stops['Zip'] == z])[['Lat','Long']]
        zipinfo = zipdata.loc[zipdata['Zip'] == z]

        # Use DBSCAN 
        # DBSCAN estimate parameters not working well 
        if algType == "DBSCAN":
            dist, minsamples = estimateClusParamsDBSCAN(subset, zipinfo)
            clustered = obtainClust_DBSCAN(subset, dist, minsamples)
        
        # Use KMEANS to perform clustering
        elif algType == "KMEANS":
            n = estimateClusParamsKMEANS(subset, bus_dict)
            clustered = obtainClust_KMEANS(subset, n)
            
        count += 1 
        if count == stop_point:
            break

        results_zips = appendClusters(results_zips, clustered)
    return results_zips

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

#################################################################
# Main
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
depot, stops, zipdata, schools, phonebook, bus_dict = setup_data(prefix+'depot_geocodes.csv', 
                                                       prefix+'stop_geocodes_fixed.csv', prefix+'zipData.csv', 
                                                       prefix+'school_geocodes_fixed.csv', prefix+'totalPhoneBook.csv', 
                                                       prefix+'dist_bus_capacities.csv')

zipClusteringResults = zipBasedClustering(stops, zipdata, bus_dict, "KMEANS")
schoolClusterResults = schoolBasedClustering(phonebook, bus_dict)
toFile(schoolClusterResults)

n = estimateClusParamsKMEANS(schools, bus_dict)
results = obtainClust_KMEANS(schools, n)
outputResults(results, 10)






#temp = pd.DataFrame(temp)
#temp.to_csv("temp.csv", encoding='utf-8', index=False)