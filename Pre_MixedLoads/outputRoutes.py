import pandas as pd 

def outputRoutes(route, geocodes):
    output = geocodes.iloc[route,:]    
    file = open("temp" + ".txt", "w") 
    
    for index, row in output.iterrows():
        file.write(str(str(row["Lat"]) + "," + str(row["Long"]) + "\n"))
    file.close()
    return output

prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
all_geocodesFile = prefix+'all_geocodes.csv'
geocodes = pd.read_csv(all_geocodesFile)
output_routes = outputRoutes(school_route + stud_route, geocodes)
