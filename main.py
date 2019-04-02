import constants
from locations import Student
from mixedloads import mixed_loads
import pickle
import random
from setup import setup_buses, setup_stops, setup_students
from generateroutes import generate_routes
from validation import full_verification
from busassignment import assign_buses
import numpy as np

def main():
    #prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//csvs//"
    prefix = "data//"
    output = setup_students([prefix+'phonebook_parta.csv',
                             prefix+'phonebook_partb.csv'],
                             prefix+'all_geocodes.csv',
                             prefix+'stop_geocodes_fixed.csv',
                             prefix+'school_geocodes_fixed.csv',
                             prefix+'bell_times.csv')
    students = output[0]
    schools_students_map = output[1]
    all_schools = output[2]
    stops = setup_stops(schools_students_map)
    cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
    #So far, we are using 0 of each contract size.
    #This will get incremented when the schools get routed.
    #contr_counts = [[8, 0], [12, 0], [25, 0], [39, 0], [65, 0]]
    #This option only allows using the larger buses -
    #I think this is preferred by LAUSD
    contr_counts = [[39, 0], [65, 0]]
    if constants.VERBOSE:
        print(len(students))
        print(len(schools_students_map))
        print(cap_counts)

    routes = generate_routes(all_schools)
    
    print("Number of routes: " + str(len(routes)))
    
    #full_verification(all_routes, print_result = True)
    
    #saving = open(("output//refactor"+str(int(constants.MAX_TIME/60))+"p8unbusedcloseschool.obj"), "wb")
    #pickle.dump(all_routes, saving)
    #saving.close()
    
    #before_splitting = len(all_routes)
    
    #out = assign_buses(all_routes, cap_counts)
    #used = out[0]
    #print("Number of buses used: " + str(used))
    #print("Leftover buses: " + str(cap_counts))
    
    #print("Buses saved next time around: " + str(mixed_loads(out[1])))
    #full_verification(out[1], print_result = True)
    #print("Original length: " + str(len(all_routes)))
    
    #return (out[1], before_splitting)
    return routes
    
num_routes = [[], []]
routes_returned = None
for i in range(1):
    routes_returned = main()
    lengths = np.array([r.length for r in routes_returned])
    print(np.mean(lengths))
    #[routes_returned, before_splitting] = main()
    #saving = open(("output//greedymlmove"+str(mins)+"p8busedcloseschool"+".obj"), "wb")
    #pickle.dump(routes_returned, saving)
    #num_routes[0].append(before_splitting)
    #num_routes[1].append(len(routes_returned))
    #print(num_routes)
    #saving.close()