import numpy as np

def mins_since_midnight(time_string):  #bit of a hack unfortunately
    parts = time_string.split(":")
    mins = int(parts[0].strip())*60
    mins += int(parts[1][:2])
    return mins

prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//"

addresses = open(prefix + 'csvs//geocoded_stops_reformatted.csv', 'r')
geocodes = open(prefix + 'csvs//all_geocodes.csv', 'r')
cost_center_geocodes = open(prefix + 'csvs//school_geocodes.csv', 'r')
cost_center_times = open(prefix + 'csvs//bell_times.csv', 'r')
address_geocode_map = dict()
geocode_index_map = dict()
cost_center_geocode_map = dict()
cost_center_belltime_map = dict()

#track index of geocode in travel time matrix
#dictionary maps "long;lat" to index in the matrix
#there are some duplicate geocodes, but their rows
#are identical so this is acceptable.

#also track map from addresses to geocodes

#additionally track map from cost centers to geocodes

count = 0

for geocode in geocodes.readlines():
    geocode_index_map[geocode.strip()] = count
    count += 1
geocodes.close()
    
addresses.readline()
for address in addresses.readlines():
    fields = address.split(";")
    address_geocode_map[fields[0]] = fields[1].strip() + ";" + fields[2].strip()
addresses.close()

cost_center_geocodes.readline()
for cost_center in cost_center_geocodes.readlines():
    fields = cost_center.split(";")
    if len(fields) < 8:
        continue
    cost_center_geocode_map[fields[1]] = fields[6].strip() + ";" + fields[7].strip()
cost_center_geocodes.close()
    
cost_center_times.readline()
for cost_center in cost_center_times.readlines():
    fields = cost_center.split(";")
    if len(fields) < 5:
        continue
    cost_center_belltime_map[fields[3]] = mins_since_midnight(fields[4])
cost_center_times.close()

#cost centers missing from geocodes list provided to me
cost_center_geocode_map['1824501'] = '34.042696;-118.326214'
cost_center_geocode_map['1859603'] = '33.996564;-118.32935682137'
cost_center_geocode_map['1326003'] = '33.9728551404294;-118.404875280021'
cost_center_geocode_map['1810703'] = '34.167327936033;-118.541600668965'
cost_center_geocode_map['1859602'] = '33.996564;-118.32935682137'

#Addresses in phonebook do not have the state, but
#the addresses I used to geocode do, so adding that

def californiafy(address):
    return address[:-6] + " California," + address[-6:]


#Now actually add the stops to the routes
#Do so as tuples (stop number in route, matrix index)
#routes is a dict from route number to sets of tuples
    
#cost centers is a dict from routes to sets of school IDs

def add_stops_to_routes(filename, routes, geocode_index_map, address_geocode_map,
                        route_cost_center_map, cost_center_geocode_map,
                        cost_center_belltime_map):
    pb_part = open(filename, 'r')
    
    pb_part.readline()
    bus_col = 12
    
    for student_record in pb_part.readlines():
        fields = student_record.split(";")
        if len(fields) < bus_col:
            continue
        if fields[bus_col].strip() == "":  #not a bus rider
            continue
        if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
            continue
        if fields[bus_col + 2].strip() != "1":  #not first trip
            continue
        
        #print(student_record)
        route = int(fields[bus_col - 1])
        if route == 9500:  #walker route
            continue
        if route not in routes:
            routes[route] = set()
            route_cost_center_map[route] = set()
        stop_time = mins_since_midnight(fields[bus_col + 4])
        address = californiafy(fields[bus_col + 6])
        matrix_index = geocode_index_map[address_geocode_map[address.strip()]]
        routes[route].add((stop_time, matrix_index))
        
        cost_center = fields[1]
        if cost_center == '':  #no known cost center, punt
            continue
        if cost_center not in route_cost_center_map[route]:  #found new cost center
            route_cost_center_map[route].add(cost_center)
            belltime = 100000   #if no known belltime, put it at end of route
            if cost_center in cost_center_belltime_map:  #case where we don't have to punt
                belltime = cost_center_belltime_map[cost_center]
            geocode = cost_center_geocode_map[cost_center]
            routes[route].add((belltime - 10, geocode_index_map[geocode]))
            
        
        
routes = dict()
route_cost_center_map = dict()
add_stops_to_routes(prefix + "csvs//phonebook_parta.csv", routes,
                    geocode_index_map, address_geocode_map, route_cost_center_map,
                    cost_center_geocode_map, cost_center_belltime_map)
add_stops_to_routes(prefix + "csvs//phonebook_partb.csv", routes,
                    geocode_index_map, address_geocode_map, route_cost_center_map,
                    cost_center_geocode_map, cost_center_belltime_map)



travel_times = np.load(prefix + "travel_time_matrix.npy")

route_times = dict()

#Note: Some routes include multiple runs. The stops get reindexed starting
#at 1. As such, we store route times as a set of times, since a route might
#contain multiple runs.
for route in routes:
    stops = list(routes[route])
    stops = sorted(stops, key = lambda x: x[0])
    #print("route number " + str(route))
    #print(stops)
    route_time = 0
    for i in range(1, len(stops)):
        route_time += travel_times[stops[i][1], stops[i-1][1]]
        if route_time > 6000:
            print("route number " + str(route))
            print(stops)
            print(route_time)
    route_times[route] = route_time

    
total_time = 0
maximum = 0
minimum = 10000
total_runs = 0
for route in route_times:
    this_time = route_times[route]
    total_runs += 1
    total_time += this_time
    maximum = max(maximum, this_time)
    minimum = min(minimum, this_time)
    
print("Average route length is " + str(total_time/total_runs))
print("Maximum route length is " + str(maximum))
print("Minimum route length is " + str(minimum))