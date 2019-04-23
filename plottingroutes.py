from locations import School, Student
import numpy as np
import pickle
from gmplot import gmplot

def plot_routes(routes, geocodes, zoom):
    min_y = 1000
    max_y = -1000
    min_x = 1000
    max_x = -1000
    for r in routes:
        for stop in r.stops:
            y = geocodes[stop.tt_ind][0]
            x = geocodes[stop.tt_ind][1]
            min_y = min(y, min_y)
            max_y = max(y, max_y)
            min_x = min(x, min_x)
            max_x = max(x, max_x)
    center_x = (min_x + max_x)/2
    center_y = (min_y + max_y)/2
    gmap = gmplot.GoogleMapPlotter(center_x, center_y, zoom)
    
    for r in routes:
        path = []
        for stop in r.stops:
            path.append(geocodes[stop.tt_ind])
        for school in r.schools:
            path.append(geocodes[school.tt_ind])
        gmap.plot([p[0] for p in path], [p[1] for p in path])
    gmap.draw('test_map.html')
    
    
    

loading = open("output//routesforpresentationb.obj", "rb")
obj = pickle.load(loading)
loading.close()

vb_routes = []
for r in obj:
    to_store = False
    for school in r.schools:
        if ("VINTAGE" in school.school_name or
                ("BALBOA" in school.school_name and "LAKE" not in school.school_name)):
            to_store = True
    if to_store:
        vb_routes.append(r)


geocodes_file = open("data//all_geocodes.csv", "r")
geocodes = []
for code in geocodes_file.readlines():
    latlong = code.split(";")
    if "\n" in latlong[1]:
        latlong[1] = latlong[1][:-2]
    latlong[0] = float(latlong[0])
    latlong[1] = float(latlong[1])
    geocodes.append(latlong)
geocodes_file.close()

plot_routes(vb_routes, geocodes, 13)