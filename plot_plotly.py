import plotly
import plotly.graph_objs as go
from plotly.offline import *
import pickle
import pandas as pd

mapbox_access_token = 'pk.eyJ1IjoiY3VoYXV3aHVuZyIsImEiOiJjanV5Z3lmeDIweTU2M3pqd2R2c244cWZiIn0.7UqrnYaqeh59icXyuDGT6Q'
prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"

with open(prefix+'routes_returned.pickle', 'rb') as handle:
    routes_returned = pickle.load(handle)

with open(prefix+'schoolnames_map.pickle', 'rb') as handle:
    SCHOOLNAME_MAP = pickle.load(handle)

geocodes = pd.read_csv(prefix+'all_geocodes.csv')
STOP_NAME = pd.read_csv(prefix+'stop_names.csv')
LA_coord = [34.052235, -118.243683]

def get_center_geolocs(total_geos):
    return [sum(total_geos.Lat)/len(total_geos), sum(total_geos.Long)/len(total_geos)]

# Plot routes, stops and schools
def plot_routes(routes, filename):
    
    schools_geo = set()
    stops_geo = set()
    
    for route in routes: 
        schools_geo.update(route.schools_to_visit)
        stops_geo.update([stop[0] for stop in route.stops_path])
    
    schools_geo_df = geocodes.iloc[list(schools_geo),:]
    schools_geo_df.insert(0, "Name", [SCHOOLNAME_MAP[school] for school in schools_geo])
    
    stops_geo_df = geocodes.iloc[list(stops_geo),:]
    stops_geo_df.insert(0, "Name", [STOP_NAME.iloc[stop]['ADDRESS'] for stop in stops_geo])

    all_points = schools_geo_df[['Lat','Long']].append(stops_geo_df[['Lat','Long']]).round(6)
    center_coords = get_center_geolocs(all_points)
        
    data = [
        # Plot schools 
        go.Scattermapbox(
            name='Schools cluster',
            lat=schools_geo_df.Lat,
            lon=schools_geo_df.Long,
            mode='markers+text',
            marker=go.scattermapbox.Marker(
                size=10,
                color='rgb(255, 0, 0)',
                opacity=0.7
            ),
            text=schools_geo_df.Name,    
            textposition="middle right",
            hoverinfo = 'text'
        ),
        
        # Plot stops
        go.Scattermapbox(
            name='Stops',
            lat=stops_geo_df.Lat,
            lon=stops_geo_df.Long,
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=12,
                color='rgb(0, 0, 255)',
                opacity=0.7
            )
        )
    ]
    
    # Plot routes
    route_paths = list()
    for i, current_route in enumerate(routes):
        
        points_geoloc = geocodes.iloc[[sch[0] for sch in current_route.schools_path] + [stop[0] for stop in current_route.stops_path],: ]
        points_geoloc = points_geoloc.round(6)
        
        school_info = list()
        for j, sch in enumerate([sch[0] for sch in current_route.schools_path]):
            if j == 0:
                school_info.append(str(SCHOOLNAME_MAP[sch]) + " -- START")
            else:
                school_info.append(str(SCHOOLNAME_MAP[sch]) + " -- " + str(current_route.stops_path[j]))

        stop_info = list()
        for j, stop in enumerate([stop[0] for stop in current_route.stops_path]):
            stop_info.append(str(STOP_NAME.loc[stop]["ADDRESS"]) + " -- " + str(current_route.stops_path[j]))
        
    
        route_paths.append(
            go.Scattermapbox(
                visible = True,
                opacity = 1,
                name = "Route " + str(i), 
                lat = list(points_geoloc.Lat),
                lon = list(points_geoloc.Long),
                mode = 'lines',
                text = school_info + stop_info
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
    
