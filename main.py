import constants
from greedymoves import make_greedy_moves
from locations import Student
from mixedloads import mixed_loads
import pickle
import random
from setup import setup_buses, setup_stops, setup_students
from generateroutes import generate_routes
from validation import full_verification
from busassignment import assign_buses
import numpy as np

def main(partial_route_plan = None):
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

    routes = generate_routes(all_schools, partial_route_plan)
    
    make_greedy_moves(routes)
    
    to_delete = set()
    for route in routes:
        if len(route.stops) == 0:
            to_delete.add(route)
    for route in to_delete:
        print("Saved one")
        routes.remove(route)
    
    if constants.VERBOSE:
        print("Number of routes: " + str(len(routes)))
    
    all_verified = True
    for route in routes:
        if not route.feasibility_check(verbose = True):
            all_verified = False
    if constants.VERBOSE:
        print("All routes verified.")
    
    #full_verification(all_routes, print_result = True)
    
    #saving = open(("output//greedymoves.obj"), "wb")
    #pickle.dump(routes, saving)
    #saving.close()
    
    #before_splitting = len(all_routes)
    
    #out = assign_buses(routes, cap_counts)
    #used = out[0]
    #print("Number of buses used: " + str(used))
    #print("Leftover buses: " + str(cap_counts))
    
    #print("Buses saved next time around: " + str(mixed_loads(out[1])))
    #full_verification(out[1], print_result = True)
    #print("Original length: " + str(len(all_routes)))
    
    return routes
    #return (routes, out[1])
    
routes_returned = None

for i in range(1):
    #constants.SCH_DIST_WEIGHT = random.random()*1.0
    #constants.STOP_DIST_WEIGHT = random.random()*1.0
    routes_returned = main()
    pieces = 2
    while True:
        orig_length = len(routes_returned)
        print("Original length: " + str(orig_length))
        new_routes = [set() for i in range(pieces)]
        for r in routes_returned:
            new_routes[int(random.random()*pieces)].add(r)
            #if random.random() < .5:
            #    new_routes1.add(r)
            #else:
            #    new_routes2.add(r)
        new_plans = []
        new_lengths = []
        for t in range(pieces):
            new_plans.append(main(new_routes[t]))
            new_lengths.append(len(new_plans[-1]))
        new_lengths = np.array(new_lengths)
        best_length = np.min(new_lengths)
        print(new_lengths)
        if orig_length <= best_length:
            continue
        for t in range(pieces):
            if new_lengths[t] == best_length:
                routes_returned = new_plans[t]
                saving = open(("output//greedymoves.obj"), "wb")
                pickle.dump(routes_returned, saving)
                saving.close()
                break
                
        #new_plan1 = main(new_routes1)
        #new_plan2 = main(new_routes2)
        #new_length1 = len(new_plan1)
        #new_length2 = len(new_plan2)
        #print("New length 1: " + str(new_length1))
        #print("New length 2: " + str(new_length2))
        #if orig_length <= new_length1 and orig_length <= new_length2:
        #    continue
        #if new_length1 < new_length2:
        #    routes_returned = new_plan1
        #else:
        #    routes_returned = new_plan2
        #saving = open(("output//partialreplacedub.obj"), "wb")
        #pickle.dump(routes_returned, saving)
        #saving.close()
        
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
    [unbused, bused] = main()
    saving = open(("output//stopdiscretizedb.obj"), "wb")
    pickle.dump(bused, saving)
    saving.close()