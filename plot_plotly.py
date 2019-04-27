import plotly
import plotly.graph_objs as go
from plotly.offline import *
import pickle
import pandas as pd

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"
with open(prefix+'routes_returned.pickle', 'rb') as handle:
    routes_returned = pickle.load(handle)

all_geocodesFile = prefix+'all_geocodes.csv'
geocodes = pd.read_csv(all_geocodesFile)

stop_namesFile = prefix+'stop_names.csv'
stop_names = pd.read_csv(stop_namesFile)

mapbox_access_token = 'pk.eyJ1IjoiY3VoYXV3aHVuZyIsImEiOiJjanV5Z3lmeDIweTU2M3pqd2R2c244cWZiIn0.7UqrnYaqeh59icXyuDGT6Q'
LA_coord = [34.052235, -118.243683]

def get_center_geolocs(total_geos):
    return [sum(total_geos.Lat)/len(total_geos), sum(total_geos.Long)/len(total_geos)]

def plot_routes(schools_geo, stops_geo, routes, filename):
    
    points_geoloc = schools_geo[['Lat','Long']].append(stops_geo[['Lat','Long']]).round(6)
    center_coords = get_center_geolocs(points_geoloc)
        
    data = [
        # Plot schools 
        go.Scattermapbox(
            name='Schools cluster',
            lat=schools_geo.Lat,
            lon=schools_geo.Long,
            mode='markers+text',
            marker=go.scattermapbox.Marker(
                size=10,
                color='rgb(255, 0, 0)',
                opacity=0.7
            ),
            text=schools_geo.Name,    
            textposition="middle right",
            hoverinfo = 'text'
        ),
        
        # Plot stops
        go.Scattermapbox(
            name='Stops cluster',
            lat=stops_geo.Lat,
            lon=stops_geo.Long,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                color='rgb(0, 0, 255)',
                opacity=0.7
            )
        )
    ]
    
    # Plot routes
    route_paths = []
    for i, current_route in enumerate(routes):
        
        points_geoloc = geocodes.iloc[current_route.path,: ]
        diff = abs(len(current_route.path_info) - len(current_route.path))
        stop_info = ["START"] * diff + current_route.path_info
        
        for j, stop in enumerate(current_route.path):
            stop_info[j] = str(stop_names.loc[stop]["ADDRESS"]) + " -- " + str(stop_info[j])
        
        route_paths.append(
            go.Scattermapbox(
                visible = True,
                opacity = 1,
                name = "Route " + str(i),
                lon = list(points_geoloc.Long),
                lat = list(points_geoloc.Lat),
                mode = 'lines',
                text = stop_info
            )
        )
    
    # Layout settings
    layout = go.Layout(
        title = filename + " routes",
        autosize=True,
        hovermode=None,
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=center_coords[0],
                lon=center_coords[1]
            ),
            pitch=0,
            zoom=10,
            style='light'
        ),
    )
    
    fig = go.Figure(data=route_paths+data, layout=layout)
    plotly.offline.plot(fig, filename=str(filename)+'.html')
    

