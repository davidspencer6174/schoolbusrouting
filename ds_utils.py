import ds_constants
import itertools
import numpy as np
import copy 

#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

#Bit of a hack to compute seconds since midnight
def timesecs(time_string):
    pieces = time_string.split(':')
    if len(pieces) < 2:
        return 100000
    minutes = int(pieces[1][:2])  #minutes
    minutes += 60*int(pieces[0])  #hours
    if 'p' in pieces[1].lower():  #PM
        minutes += 12*60
    return minutes*60

def stud_trav_time_array(route_plan):
    stud_trav_times = [r.student_travel_times() for r in route_plan]
    #Flatten this list and convert to an np array
    stud_trav_times = np.array(list(itertools.chain(*stud_trav_times)))
    return stud_trav_times

#Determines a closest pair of locations in from_iter and to_iter
#from_iter and to_iter should both be iterables of Students and/or Schools
#optionally, can require a specific age type if to_iter has Students
def closest_pair(from_iter, to_iter, age_type = None):
    opt_dist = 100000
    opt_from_loc = None
    opt_to_loc = None
    for from_loc in from_iter:
        for to_loc in to_iter:
            if (ds_constants.TRAVEL_TIMES[from_loc.tt_ind,
                                       to_loc.tt_ind] < opt_dist and
                (age_type == None or to_loc.type == age_type)):
                opt_dist = ds_constants.TRAVEL_TIMES[from_loc.tt_ind,
                                                  to_loc.tt_ind]
                opt_from_loc = from_loc
                opt_to_loc = to_loc
    return opt_from_loc, opt_to_loc

def closest_addition(locations, betw_iter, available_time, alpha, age_type = None):
    opt_cost = 100000
    opt_dist = 100000
    opt_loc = None
    opt_ind = -1
    for i in range(len(locations) - 1):
        for loc in betw_iter:
            if ((ds_constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                ds_constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                ds_constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                (ds_constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha) < opt_cost and
                ds_constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                ds_constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                ds_constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < available_time and
                (age_type == None or loc.type == age_type)):
            #if (ds_constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
            #    ds_constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
            #    ds_constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < opt_dist and
            #    (age_type == None or loc.type == age_type)):
                opt_cost = ((ds_constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            ds_constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                           ds_constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                            (ds_constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha))
                opt_dist = (ds_constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            ds_constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                            ds_constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])
                opt_loc = loc
                opt_ind = i
                if opt_dist == 0:
                    break
        if opt_dist == 0:
            break
    return (opt_loc, opt_ind, opt_dist)

#Checks if two stop objects are isomorphic, even if they are
#not the same object in memory.
def isomorphic(stop1, stop2):
    return(stop1.type == stop2.type and
           stop1.school.tt_ind == stop2.school.tt_ind and
           stop1.tt_ind == stop2.tt_ind)

#Checks to see which ds_routes in the first ds_route plan share at least
#one stop with the passed-in ds_route.
#Does not require pointer equality for stops, only object value
#equality.
def overlapping_ds_routes(ds_route_plan, ds_route):
    out = set()
    for compare_ds_route in ds_route_plan:
        for stop1 in compare_ds_route.stops:
            for stop2 in ds_route.stops:
                if isomorphic(stop1, stop2):
                    out.add(compare_ds_route)
    return out

def full_comparison(rp1, rp2):
    tot = 0
    for r in rp1:
        out = overlapping_ds_routes(rp2, r)
        if len(out) == 1:
            tot += 1
    print("ds_route Plan 2 has " + str(tot) + " ds_routes that are subds_routes "+
          "of ds_routes in ds_route Plan 1.")
    tot = 0
    for r in rp2:
        out = overlapping_ds_routes(rp1, r)
        if len(out) == 1:
            tot += 1
    print("ds_route Plan 1 has " + str(tot) + " ds_routes that are subds_routes "+
          "of ds_routes in ds_route Plan 2.")
    tot = 0
    iso_stops_same = []
    for r in rp1:
        out = overlapping_ds_routes(rp2, r)
        if len(out) == 1:
            r2 = list(out)[0]
            out2 = overlapping_ds_routes(rp1, r2)
            if len(out2) == 1:
                r1 = list(out)[0]
                tot += 1
                stop_inds = set()
                for stop in r2.stops:
                    stop_inds.add(stop.tt_ind)
                iso_stops_same.append(len(stop_inds))
    print(str(tot) + " ds_routes appear in both ds_route plans.")
    print("Number of stops in these common ds_routes:")
    iso_stops_same.sort()
    print(iso_stops_same)
    
def two_opt(ds_route):
#    print("--------- Two-opt")
    num_stops = len(ds_route.stops)
    orig_length = ds_route.length
    for ind1 in range(num_stops):
        for ind2 in range(ind1+2, num_stops):
            ds_route.stops[ind1:ind2] = ds_route.stops[ind1:ind2][::-1]
            ds_route.recompute_length()
            if ds_route.length < orig_length:
                print("Improved")
                two_opt(ds_route)
                return
            ds_route.stops[ind1:ind2] = ds_route.stops[ind1:ind2][::-1]
    ds_route.recompute_length()
          
#Determines mean student travel time
def mstt(ds_route_plan):
    trav_times = []
    for ds_route in ds_route_plan:
        trav_times.extend(ds_route.student_travel_times())
    trav_times = np.array(trav_times)
    return np.mean(trav_times)
    
#Entries in to_do determine whether we make greedy moves, do two_opt,
#and do Park/Kim's mixed-load procedure.
#ds_route_plan should be a list.
def improvement_procedures(route_plan, to_do = [True, True, True]):
#    print(" -- Running Improvement Procedures")
    ori_route_plan = copy.deepcopy(route_plan)
    from ds_greedymoves import make_greedy_moves
    from ds_mixedloads import mixed_loads
    while True:
        prev_num_ds_routes = len(route_plan)
        prev_mean_trav = mstt(route_plan)
        if to_do[0]:
            make_greedy_moves(route_plan)
        if to_do[1]:
            for route in route_plan:
                two_opt(route)
        if to_do[2]:
            mixed_loads(route_plan)
        if (len(route_plan) == prev_num_ds_routes and mstt(route_plan) == prev_mean_trav):
            break
    return route_plan