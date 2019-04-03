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
    
    if constants.VERBOSE:
        print("Number of routes: " + str(len(routes)))
    
    all_verified = True
    for route in routes:
        if not route.feasibility_check(verbose = True):
            all_verified = False
    if constants.VERBOSE:
        print("All routes verified.")
    
    #full_verification(all_routes, print_result = True)
    
    saving = open(("output//stopdiscretizedub.obj"), "wb")
    pickle.dump(routes, saving)
    saving.close()
    
    #before_splitting = len(all_routes)
    
    out = assign_buses(routes, cap_counts)
    used = out[0]
    print("Number of buses used: " + str(used))
    #print("Leftover buses: " + str(cap_counts))
    
    #print("Buses saved next time around: " + str(mixed_loads(out[1])))
    #full_verification(out[1], print_result = True)
    #print("Original length: " + str(len(all_routes)))
    
    #return (out[1], before_splitting)
    return (out[1], routes)
    
routes_returned = None
for i in range(1):
    #constants.SCH_DIST_WEIGHT = random.random()*1.0
    #constants.STOP_DIST_WEIGHT = random.random()*1.0
    routes_returned = main()
    if constants.VERBOSE:
        lengths = np.array([r.length for r in routes_returned])
        print("Mean length: " + str(np.mean(lengths)))
        occs = np.array([r.occupants for r in routes_returned])
        print("Total occupants: " + str(np.sum(occs)))
        numstops = np.array([len(r.stops) for r in routes_returned])
        print("Total number of stops visited: " + str(np.sum(numstops)))
    #print(str(constants.SCH_DIST_WEIGHT) + " " +
    #      str(constants.STOP_DIST_WEIGHT) + " " + 
    #      str(len(routes_returned)))
    print(str(len(routes_returned)))
    [bused, unbused] = main()
    saving = open(("output//stopdiscretizedb.obj"), "wb")
    pickle.dump(bused, saving)
    saving.close()