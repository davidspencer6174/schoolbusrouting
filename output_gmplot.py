from gmplot import gmplot



gmap = gmplot.GoogleMapPlotter(34.052235, -118.243683, 13)

# Scatter points
schools_lats, schools_longs = zip(*schools_geo)
stops_lats, stops_longs = zip(*stops_geo)

gmap.scatter(schools_lats, schools_longs, '#A93226', size=250, marker=False)
gmap.scatter(stops_lats, stops_longs, '#3B0B39', size=200, marker=False)

count = 0 
for route_group in routes_geo: 
    route_lats, route_longs = zip(*route_group)
    gmap.plot(route_lats, route_longs, 'cornflowerblue', edge_width=6)
    
    new = 0
    for i, row in enumerate(route_group):
        new += 1
        gmap.marker(row[0], row[1], title="A street corner in Seattle")


    gmap.draw(str(count) + " -- my_route.html")
    count += 1 

for route in routes_geo: 
    route_lats, route_longs = zip(*route)
    gmap.plot(route_lats, route_longs, 'cornflowerblue', edge_width=6)




gmap.draw('total_routes.html')
    
    
    


gmap = gmplot.GoogleMapPlotter(34.052235, -118.243683, 13)
gmap.marker(47.61028142523736, -122.34147349538826, title="A street corner in Seattle")
st="testmap.html"
gmap.draw(st)



import pickle

with open('routes_returned.pickle', 'wb') as handle:
    pickle.dump(routes_returned, handle, protocol=pickle.HIGHEST_PROTOCOL)

import plotly