import numpy as np

prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//"

addresses = open(prefix + 'csvs//geocoded_stops_reformatted.csv', 'r')
geocodes = open(prefix + 'csvs//all_geocodes.csv', 'r')
address_geocode_map = dict()
geocode_index_map = dict()

#track index of geocode in travel time matrix
#dictionary maps "long;lat" to index in the matrix
#there are some duplicate geocodes, but their rows
#are identical so this is acceptable.

#also track map from addresses to geocodes

count = 0

for geocode in geocodes.readlines():
    geocode_index_map[geocode.strip()] = count
    count += 1
addresses.readline()
for address in addresses.readlines():
    fields = address.split(";")
    address_geocode_map[fields[0]] = fields[1] + ";" + fields[2].strip()
addresses.close()
geocodes.close()

#Addresses in phonebook do not have the state, but
#the addresses I used to geocode do, so adding that

def californiafy(address):
    return address[:-6] + " California," + address[-6:]

def mins_since_midnight(time_string):  #bit of a hack unfortunately
    parts = time_string.split(":")
    mins = int(parts[0].strip())*60
    mins += int(parts[1][:2])
    return mins

#Now actually add the stops to the routes
#Do so as tuples (stop time, stop number in route, matrix index)
#routes is a dict from route number to sets of tuples
#Stop time expressed as minutes since midnight

def add_stops_to_routes(filename, routes, geocode_index_map, address_geocode_map):
    pb_part = open(filename, 'r')
    
    phonebook_header = pb_part.readline()
    bus_col = 12
    
    for student_record in pb_part.readlines():
        fields = student_record.split(";")
        if len(fields) < bus_col:
            continue
        if fields[bus_col].strip() == "":  #not a bus rider
            continue
        if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
            continue
        
        #print(student_record)
        route = int(fields[bus_col - 1])
        if route == 9500:  #walker route
            continue
        if route not in routes:
            routes[route] = set()
        stop_number = int(fields[bus_col + 3])
        stop_time = mins_since_midnight(fields[bus_col + 4])
        address = californiafy(fields[bus_col + 6])
        matrix_index = geocode_index_map[address_geocode_map[address.strip()]]
        routes[route].add((stop_time, stop_number, matrix_index))
        
routes = dict()
add_stops_to_routes(prefix + "csvs//phonebook_parta.csv", routes,
                    geocode_index_map, address_geocode_map)
add_stops_to_routes(prefix + "csvs//phonebook_partb.csv", routes,
                    geocode_index_map, address_geocode_map)





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
    route_time_set = set()
    for i in range(1, len(stops)):
        if stops[i][1] == 1:  #need to store the route time and reset count
            route_time_set.add(route_time)
            route_time = 0
            continue  #don't consider travel time here, no students ride
        route_time += travel_times[stops[i][2], stops[i-1][2]]
        if route_time > 6000:
            print("route number " + str(route))
            print(stops)
            print(route_time_set)
    route_times[route] = route_time_set

    
total_time = 0
maximum = 0
minimum = 10000
total_runs = 0
for route in route_times:
    for this_time in route_times[route]:
        total_runs += 1
        total_time += this_time
        maximum = max(maximum, this_time)
        minimum = min(minimum, this_time)
    
print("Average route length is " + str(total_time/total_runs))
print("Maximum route length is " + str(maximum))
print("Minimum route length is " + str(minimum))