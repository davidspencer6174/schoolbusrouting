from collections import Counter
import pandas as pd 
import pickle

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

def displayLAUSDRoutes(school_name):
    temp = phonebook.loc[phonebook['Cost_Center_Name'] == school_name]
    temp = temp.sort_values(by=['AM_Route', 'AM Time'])
    routes = list(Counter(temp['AM_Route']).keys())
    routes = [x for x in routes if str(x) != 'nan']
    cost_center_number = temp.iloc[0]['Cost_Center']

    for route in routes:
#        print("Route: " + str(route))
        subset = temp.loc[temp['AM_Route'] == route]
        subset = subset[['AM_Stop_Address', 'AM Stop']]
        subset = subset.drop_duplicates()
        
        link = "https://www.google.com/maps/dir"

        for idx, stop in subset.iterrows():
            point = californiafy(stop['AM_Stop_Address'])
            point_geoloc = STOPS_CODES_MAP[point]
            point_geoloc = point_geoloc.split(";")
            link += ("/" + str(point_geoloc[0]) + "," + str(point_geoloc[1]))
        
        school_geoloc = SCHOOLS_CODES_MAP[cost_center_number]
        school_geoloc = school_geoloc.split(";")
        link += ("/" + str(school_geoloc[0]) + "," + str(school_geoloc[1]))
        print(link)
    
prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/'
phonebookFile = prefix+'totalPhoneBook.csv'
phonebook = pd.read_csv(phonebookFile, dtype={"RecordID": str, 'Prog': str, 'Cost_Center': str, "AM_Route": str, 'Lat': float, 'Long': float}, low_memory=False)
phonebook['Cost_Center_Name'] = phonebook['Cost_Center_Name'].str.strip()
phonebook = phonebook[phonebook['AM_Route'] != str(9500)]

with open(prefix+'mixed_load_data/stops_codes_map' ,'rb') as handle:
    STOPS_CODES_MAP = pickle.load(handle)

with open(prefix+'mixed_load_data/schools_codes_map','rb') as handle:
    SCHOOLS_CODES_MAP = pickle.load(handle)

displayLAUSDRoutes('REVERE CMS')
print("---------------------------")
displayLAUSDRoutes('REVERE STM MAG')
