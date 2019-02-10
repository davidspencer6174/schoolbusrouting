# Convert clusters from df into object
def unpackClusters(clusters):
    schoollist = []
    stoplist = []
    schools = pd.DataFrame(sorted(clusters["School_Clustered"], key = lambda x:x[2]))
    stops = pd.DataFrame(sorted(clusters["Stops_Clustered"], key = lambda x:x[2]))
    
    for i in list(schools[2].drop_duplicates()):
        subset = schools[(schools[2] == i)]
        points1 = subset.iloc[:, 0:2]
        schoollist.append(Cluster('school', points1))
        
    for j in list(stops[2].drop_duplicates()):
        subset = stops[(stops[2] == j)]
        points2 = subset.iloc[:, 0:2]
        stoplist.append(Cluster('stops', points2))
    return schoollist, stoplist

class Cluster:         
    def __init__(self, clust_type, points):
        self.clust_type = clust_type
        self.points = points
        self.cluster_center = None
                
    def get_num_points(self):
        return len(self.points)
    
    def get_cluster_center(self):
        x = np.sum(self.points[0])/(len(self.points))
        y = np.sum(self.points[1])/(len(self.points))  
        self.cluster_center = [x,y]
        
        
def setup_clusters(s)







import osrm

list_coord = [[21.0566163803209, 42.004088575972],[21.3856064050746, 42.0094518118189], [20.9574645547597, 41.5286973392856], [21.1477394809847, 41.0691482795275], [21.5506463080973, 41.3532256406286]]

list_id = ['name1', 'name2', 'name3', 'name4', 'name5']
time_matrix, snapped_coords = osrm.table(list_coord,
                                  				  ids_origin=list_id,
                                  				  output='dataframe')



def cluster_travel_time_matrix(cluster):
    

# schoollist and stoplist from main.py
centerpoints = list()
    
for i in schoollist:
    centerpoints.append(i.get_cluster_center())
    
for j in stoplist: 
    centerpoints.append(j.get_cluster_center())
    
time_matrix, snapped_coords = osrm.table(centerpoints, output='dataframe')