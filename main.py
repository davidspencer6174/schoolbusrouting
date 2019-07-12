import constants
import copy
from greedymoves import make_greedy_moves
from time import process_time
from locations import Student
from mixedloads import mixed_loads
import pickle
import random
from savingsbasedroutegeneration import clarke_wright_savings
from setup import setup_buses, setup_stops, setup_students
from generateroutes import generate_routes
from busassignment_bruteforce import assign_buses
import numpy as np
from utils import improvement_procedures, stud_trav_time_array, mstt

global start_time

def main(method, sped, partial_route_plan = None, permutation = None,
         improve = False, to_bus = False):
    #prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//csvs//"
    prefix = "data//"
    output = setup_students(prefix+'RGSP_Combined.csv',
                            prefix+'all_geocodes.csv',
                            prefix+'stop_geocodes_fixed.csv',
                            prefix+'school_geocodes_fixed.csv',
                            prefix+'bell_times.csv',
                            sped)
    students = output[0]
    schools_students_map = output[1]
    all_schools = output[2]
    stops = setup_stops(schools_students_map)
    buses = setup_buses(prefix+'dist_bus_capacities_sped.csv', sped)
    if constants.VERBOSE:
        print(len(students))
        print(len(schools_students_map))
        
    routes = None
    
    if method == "mine":
        routes = generate_routes(all_schools, permutation = permutation,
                             partial_route_plan = partial_route_plan)
    
    if method == "savings":
        routes = clarke_wright_savings(all_schools)

    for route in routes:
        assert route.feasibility_check(verbose = True)
    
    if improve:
        improvement_procedures(routes)
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
        
    #As per dicussions in early July 2019, we decided
    #not to have the program attempt bus assignment
    #for special ed.
    if to_bus and not sped:
        routes = assign_buses(routes, buses)
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
        
    if improve:
        improvement_procedures(routes)
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
    
    if constants.VERBOSE:
        print("Number of routes: " + str(len(routes)))
    
    all_verified = True
    for route in routes:
        if not route.feasibility_check(verbose = True):
            all_verified = False
    if constants.VERBOSE:
        print("All routes verified.")
    
    return routes
    
routes_returned = None

def permutation_approach(sped, mstt_weight, iterations = 100, minutes = None):
    global start_time
    #Uncomment latter lines to use an existing permutation
    best_perm = None
    best_routes = None
    #loading_perm = open(("output//lastperm55m.obj"), "rb")
    #loading_perm = open(("output//newagerestrictionperm.obj"), "rb")
    #best_perm = pickle.load(loading_perm)
    #loading_perm.close()
    best_num_routes = 100000
    best_mstt = 100000
    score_function = lambda num_routes, plan_mstt: num_routes + mstt_weight*plan_mstt
    #score_function = lambda num_routes, plan_mstt: num_routes + 6*plan_mstt/500
    best_score = score_function(best_num_routes, best_mstt)
    
    best_mstt_per_num_routes = dict()
    
    successes = []
    new_perm = None
    for test in range(iterations):
        if test > 0:
            #Try a few swaps
            new_perm = copy.copy(best_perm)
            num_to_swap = random.randint(1, 40)
            for swap in range(num_to_swap):
                #Bias toward early stops, since these are more important
                ind1 = random.randint(0, min(40, len(new_perm) - 1))
                if random.random() < .9:
                    ind1 = random.randint(0, len(new_perm) - 1)
                ind2 = random.randint(0, len(new_perm) - 1)
                new_perm[ind1], new_perm[ind2] = new_perm[ind2], new_perm[ind1]
        #Test the route
        new_routes_returned = main("mine", sped, permutation = new_perm, improve = True, to_bus = True)
        if best_perm == None:
            all_stops = set()
            for route in new_routes_returned:
                for stop in route.stops:
                    all_stops.add(stop)
            new_perm = list(range(len(all_stops)))
            best_perm = list(range(len(all_stops)))
        new_num_routes = len(new_routes_returned)
        new_mstt = mstt(new_routes_returned)/60
        #new_score = new_num_routes + 6*new_mstt/500
        new_score = score_function(new_num_routes, new_mstt)
        if new_num_routes not in best_mstt_per_num_routes:
            best_mstt_per_num_routes[new_num_routes] = (new_mstt, new_routes_returned)
        if new_mstt < best_mstt_per_num_routes[new_num_routes][0]:
            best_mstt_per_num_routes[new_num_routes] = (new_mstt, new_routes_returned)
            print("Made an improvement")
            for num_r in best_mstt_per_num_routes:
                print((num_r, best_mstt_per_num_routes[num_r][0]))
        if (new_score < best_score):
            print("New best")
            print(new_score)
            best_perm = new_perm
            best_mstt = new_mstt
            best_num_routes = new_num_routes
            best_score = new_score
            best_routes = new_routes_returned
            #saving = open(("output//testcombining.obj"), "wb")
            #pickle.dump(best, saving)
            #saving.close()
            #saving = open(("output//testcombining.obj"), "wb")
            #pickle.dump(best_perm, saving)
            #saving.close()
            if test > 0:
                successes.append(num_to_swap)
                print(successes)
        if minutes != None and process_time() > start_time + 60*minutes:
            break
        print(str(new_num_routes) + " " + str(new_mstt))
    return best_routes    
    #final_routes = main("mine", sped, permutation = best_perm, improve = True)
    #saving = open("output//testcombining.obj", "wb")
    #pickle.dump(final_routes, saving)
    #saving.close()
    #buses = setup_buses('data//dist_bus_capacities_sped.csv', sped)
    #final_bused_routes = assign_buses(final_routes, buses)
    #improvement_procedures(final_bused_routes)
    #saving = open("output//testcombining.obj", "wb")
    #pickle.dump(final_bused_routes, saving)
    #saving.close()
    #return final_bused_routes


#Larger mstt_weights will prioritize travel time over
#the number of routes.
def vary_params(sped, mstt_weight, minutes = None):
    global start_time
    best_score = 100000000
    best_params = ()
    best_results = []
    for i in range(1000):
        #Set up parameters with some randomness
        constants.SCH_DIST_WEIGHT = random.random()*.5 + .7
        constants.STOP_DIST_WEIGHT = random.random()*.2
        constants.EVALUATION_CUTOFF = random.random()*500 - 300
        constants.MAX_SCHOOL_DIST = random.random()*600 + 800
        
        #Test these parameters
        routes_returned = main("mine", sped)
        
        #Take measurements of the result
        num_routes = len(routes_returned)
        stud_trav_times = stud_trav_time_array(routes_returned)
        mean_stud_trav_time = np.mean(stud_trav_times)/60
        
        
        
        #Set up the result to store. If it is dominated by
        #another result, we won't store it; if it dominates
        #another result, we will delete that one.
        result = (num_routes, mean_stud_trav_time,
                  constants.SCH_DIST_WEIGHT,
                  constants.STOP_DIST_WEIGHT, constants.EVALUATION_CUTOFF,
                  constants.MAX_SCHOOL_DIST)
        if num_routes + mstt_weight*mean_stud_trav_time < best_score:
            best_score = num_routes + mstt_weight*mean_stud_trav_time
            best_params = (constants.SCH_DIST_WEIGHT, constants.STOP_DIST_WEIGHT,
                           constants.EVALUATION_CUTOFF, constants.MAX_SCHOOL_DIST)
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
            print(sorted([i[:2] for i in best_results], key=lambda x:x[0]))
        print(str(constants.SCH_DIST_WEIGHT) + " " +
              str(constants.STOP_DIST_WEIGHT) + " " +
              str(constants.EVALUATION_CUTOFF) + " " +
              str(constants.MAX_SCHOOL_DIST) + " " +
              str(len(routes_returned)) + " " + 
              str(mean_stud_trav_time))
        if minutes != None and process_time() > start_time + 60*minutes:
            break
    (constants.SCH_DIST_WEIGHT, constants.STOP_DIST_WEIGHT,
     constants.EVALUATION_CUTOFF, constants.MAX_SCHOOL_DIST) = best_params
    return best_results

#Does a full run, that is, makes a route plan for special ed
#without considering buses and makes a route plan for
#magnet with consideration of buses.
def full_run(sped_mstt_weight, magnet_mstt_weight, minutes_per_segment):
    global start_time
    #First, try to find good parameters by doing quick runs that
    #don't do improvement procedures or bus assignment.
    start_time = process_time()
    vary_params(True, sped_mstt_weight, minutes = minutes_per_segment)
    start_time = process_time()
    sped_routes = permutation_approach(True, sped_mstt_weight, minutes = minutes_per_segment)
    start_time = process_time()
    vary_params(False, magnet_mstt_weight, minutes = minutes_per_segment)
    start_time = process_time()
    magnet_routes = permutation_approach(False, magnet_mstt_weight, minutes = minutes_per_segment)
    all_routes = sped_routes + magnet_routes
    print("Final number of magnet routes: " + str(len(magnet_routes)))
    print("Mean student travel time of magnet routes: " + str(mstt(magnet_routes)) + " minutes")
    print("Final number of special ed routes: " + str(len(sped_routes)))
    print("Mean student travel time of special ed routes: " + str(mstt(sped_routes)) + " minutes")
    return all_routes
    

full_run(.01, .01, .3)
#savings_routes = main("savings", improve = True, buses = False)        
#final_result = permutation_approach(False, 2000)
#vary_params()