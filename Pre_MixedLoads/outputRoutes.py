import pandas as pd 

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
all_geocodesFile = prefix+'all_geocodes.csv'
geocodes = pd.read_csv(all_geocodesFile)

def outputRoutes(cluster_school_map, routes_returned, filename):
    file = open(str(filename) + ".txt", "w")     
    for index in routes_returned:
        file.write("Schools in this cluster: \n") 
        
        for clus_school in cluster_school_map[index]:            
            file.write(str(clus_school.school_name) + "\n")
            
        for points in routes_returned[index]:
            output = geocodes.iloc[points,: ]
            
            link = "https://www.google.com/maps/dir"
            
            for ind, row in output.iterrows():
                link += ("/" + str(row['Lat']) + "," + str(row['Long']))
            
            file.write("Google Maps Link: \n")
            file.write(link)
            file.write("\n")
            file.write("\n")
        file.write("---------------------- \n")
    file.close()
            
outputRoutes(cluster_school_map_elem, routes_returned_elem, "elem_school_routes")



outputRoutes(cluster_school_map_middle, routes_returned_middle, "middle_school_routes")
outputRoutes(cluster_school_map_high, routes_returned_high, "high_school_routes")
