import pandas as pd 

def outputRoutes(route, geocodes):
    output = geocodes.iloc[route,:]    
    file = open("temp1" + ".txt", "w") 
    for index, row in output.iterrows():
        file.write(str(str(row["Lat"]) + ", " + str(row["Long"]) + "\n"))
    file.close()
    return output



prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/'
all_geocodesFile = prefix+'all_geocodes.csv'

geocodes = pd.read_csv(all_geocodesFile)
output_routes = outputRoutes(route_list[1], geocodes)

route_list = [[10776, 10494, 10868, 10501, 800, 5106, 2712, 9027, 8439, 5651, 6322, 6614],
 [10776, 10494, 10868, 10501, 1904, 2500, 3171, 3618, 3191, 5421, 4713],
 [10776, 10494, 10868, 10501, 8918, 3255, 8762, 3774, 3873]]