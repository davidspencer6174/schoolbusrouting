from gmplot import gmplot

# Place map
# Coordinates for Los Angeles

def plot_gmap(schools_geo, stops_geo, routes_geo):
    
    gmap = gmplot.GoogleMapPlotter(34.052235, -118.243683, 13)
    
    # Scatter points
    schools_lats, schools_longs = zip(*schools_geo)
    stops_lats, stops_longs = zip(*stops_geo)
    
    
    gmap.scatter(schools_lats, schools_longs, '#A93226', size=250, marker=False)
    gmap.scatter(stops_lats, stops_longs, '#3B0B39', size=200, marker=False)
    
    for route in routes_geo: 
        
        
        route_lats, route_longs = zip(*route)
        gmap.plot(route_lats, route_longs, 'cornflowerblue', edge_width=6)
    
    # Draw
    gmap.draw("my_map.html")
 
    
    