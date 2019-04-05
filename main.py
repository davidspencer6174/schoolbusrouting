import constants
import copy
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

def main(partial_route_plan = None, permutation = None):
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

    routes = generate_routes(all_schools, permutation = permutation,
                             partial_route_plan = partial_route_plan)
    
    #make_greedy_moves(routes)
    
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

def permutation_approach():
    #Uncomment latter lines to use an existing permutation
    best_perm = None
    #loading_perm = open(("output//lastperm55m.obj"), "rb")
    #best_perm = pickle.load(loading_perm)
    #loading_perm.close()
    routes_returned = main(permutation = best_perm)
    all_stops = set()
    for route in routes_returned:
        for stop in route.stops:
            all_stops.add(stop)
    if best_perm == None:
        best_perm = list(range(len(all_stops)))
    best_num_routes = len(routes_returned)
    best_time = np.sum(np.array([r.length for r in routes_returned]))
    best = routes_returned
    print(best_num_routes + " " + str(best_time/best_num_routes/60))
    successes = []
    while True:
        new_perm = copy.copy(best_perm)
        num_to_swap = random.randint(1, 3)
        for swap in range(num_to_swap):
            ind1 = random.randint(0, 40)
            if random.random() < .9:
                ind1 = random.randint(0, len(new_perm) - 1)
            ind2 = random.randint(0, len(new_perm) - 1)
            new_perm[ind1], new_perm[ind2] = new_perm[ind2], new_perm[ind1]
        new_routes_returned = main(permutation = new_perm)
        new_num_routes = len(new_routes_returned)
        new_time = np.sum(np.array([r.length for r in new_routes_returned]))
        if (new_num_routes < best_num_routes or
            (new_num_routes == best_num_routes and new_time < best_time)):
                print("New best")
                best_perm = new_perm
                best_num_routes = new_num_routes
                best_time = new_time
                best = new_routes_returned
                saving = open(("output//fixedlastinsert.obj"), "wb")
                pickle.dump(best, saving)
                saving.close()
                saving = open(("output//lastperm.obj"), "wb")
                pickle.dump(best_perm, saving)
                saving.close()
                successes.append(num_to_swap)
                print(successes)
        print(str(new_num_routes) + " " + str(new_time/new_num_routes/60))
        
best_results = []

def vary_params():
    best = 10000
    for i in range(500):
        #interesting:
        #.6168660904233182
        #.11884540775695918
        #-782.0102581987334
        #417
        #.4489310134175062
        #.0466412252275971
        #-956.9955655024021
        #418 54.11
        #.5178650537039641
        #.00696192681486929
        #-299.059132574243
        #454 48.89
        #.3945923017356171
        #.06278120044940694
        #-838.8683761471727
        #424 52.86
        constants.SCH_DIST_WEIGHT = random.random()*1.3
        constants.STOP_DIST_WEIGHT = random.random()*.3 - .1
        constants.EVALUATION_CUTOFF = random.random()*3000 - 2500
        routes_returned = main()
        if len(routes_returned) < best:
            best = len(routes_returned)
            #saving = open(("output/varyingparams.obj"), "wb")
            #pickle.dump(routes_returned, saving)
            #saving.close()
        mean_time = np.mean(np.array([r.length for r in routes_returned]))
        result = (len(routes_returned), mean_time/60, constants.SCH_DIST_WEIGHT,
                  constants.STOP_DIST_WEIGHT, constants.EVALUATION_CUTOFF)
        strictly_worse = False
        to_remove = set()
        for other_result in best_results:
            if other_result[0] <= result[0] and other_result[1] <= result[1]:
                strictly_worse = True
                break
            if result[0] <= other_result[0] and result[1] <= other_result[1]:
                to_remove.add(other_result)
        if not strictly_worse:
            best_results.append(result)
            for worse_one in to_remove:
                best_results.remove(worse_one)
            print(sorted([i[0:2] for i in best_results], key=lambda x:x[0]))
        print(str(constants.SCH_DIST_WEIGHT) + " " +
              str(constants.STOP_DIST_WEIGHT) + " " +
              str(constants.EVALUATION_CUTOFF) + " " +
              str(len(routes_returned)) + " " + 
              str(mean_time/60))
        
    
def subroutes_approach():
    for i in range(1):
        #constants.SCH_DIST_WEIGHT = random.random()*1.0
        #constants.STOP_DIST_WEIGHT = random.random()*1.0
        routes_returned = main()
        saving = open(("output//greedymoves.obj"), "wb")
        pickle.dump(routes_returned, saving)
        saving.close()
        pieces = 5
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
                new_plans.append(main(partial_route_plan = new_routes[t]))
                new_lengths.append(len(new_plans[-1]))
            new_lengths = np.array(new_lengths)
            best_length = np.min(new_lengths)
            print(new_lengths)
            if orig_length <= best_length:
                continue
            for t in range(pieces):
                if new_lengths[t] == best_length:
                    routes_returned = new_plans[t]
                    saving = open(("output//workspace.obj"), "wb")
                    pickle.dump(routes_returned, saving)
                    saving.close()
                    break
            
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
        
#permutation_approach()
vary_params()