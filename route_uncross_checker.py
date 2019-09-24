import constants
from itertools import product
import pickle
from route import Route
from setup import setup_parameters, setup_mod_caps
from utils import mstt, two_opt

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

geocodes = open("data//all_geocodes.csv", "r")
codes = []
for code in geocodes.readlines():
    codes.append(code.strip())

def ccw(p1, p2, p3):
    return (p3[1] - p1[1])*(p2[0] - p1[0]) > (p2[1] - p1[1])*(p3[0] - p1[0])

#Determine whether two line segments cross
#Due to
#https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
def line_segments_cross(p1, p2, p3, p4):
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

def virtual_crossing(r1, r2, i1, i2):
    d_current = trav_time(r1.stops[i1], r1.stops[i1 + 1]) + trav_time(r2.stops[i2], r2.stops[i2 + 1])
    d_new = trav_time(r1.stops[i1], r2.stops[i2 + 1]) + trav_time(r2.stops[i2], r1.stops[i1 + 1])
    return (d_new < d_current)

def get_lat_long(stop):
    code = codes[stop.tt_ind]
    latlong = code.split(";")
    latlong[0] = float(latlong[0])
    latlong[1] = float(latlong[1])
    return latlong

def route_pair_crossings(r1, r2):
    crossings = []
    for i1 in range(0, len(r1.stops) - 1):
        for i2 in range(0, len(r2.stops) - 1):
            p1 = get_lat_long(r1.stops[i1])
            p2 = get_lat_long(r1.stops[i1 + 1])
            p3 = get_lat_long(r2.stops[i2])
            p4 = get_lat_long(r2.stops[i2 + 1])
            #if virtual_crossing(r1, r2, i1, i2):
            #    crossings.append((i1, i2))
            if line_segments_cross(p1, p2, p3, p4):
                crossings.append((i1, i2))
    return crossings
   
#Returns -1 if the uncrossing is longer
#Otherwise, returns a tuple with six entries: the mean amount of
#time saved for each student in seconds, the worst ratio of the travel
#times to the maximum travel times, the worst overcrowding rates
#for each of the two possible assignments of the buses to the routes,
#and the two new routes (without buses assigned)
def try_uncrossing(r1, r2, i1, i2):
    new_r1 = Route()
    new_r2 = Route()
    for i in range(i1):
        new_r1.add_stop(r1.stops[i])
    for i in range(i2, len(r2.stops)):
        new_r1.add_stop(r2.stops[i])
    for i in range(i2):
        new_r2.add_stop(r2.stops[i])
    for i in range(i1, len(r1.stops)):
        new_r2.add_stop(r1.stops[i])
    #If the school combination was invalid, not
    #all stops will make it on
    if len(new_r1.stops) + len(new_r2.stops) < len(r1.stops) + len(r2.stops):
        return -1
    savings = mstt([r1, r2]) - mstt([new_r1, new_r2])
    #If the new routes don't save time on average, no point
    #Note: savings <= 0 sometimes allows trivial swaps to
    #sneak by due to floating point error, so use savings <= 1
    if savings <= 1:
        #if r1.length + r2.length > new_r1.length + new_r2.length:
        #    print("the weird case")
        return -1
    #Determine by how much (if at all) the time constraints are violated
    worst_extra_time_ratio = max(new_r1.length/new_r1.max_time,
                                 new_r2.length/new_r2.max_time)
    #Determine whether the uncrossing mixes elementary
    #and high school students
    elem_high_mixed = ((new_r1.e_no_h and new_r1.h_no_e) or
                       (new_r2.e_no_h and new_r2.h_no_e))
    #In the special ed case, buses are not assigned, so we return
    #zeros for the capacity parts.
    if r1.bus == None or r2.bus == None:
        return (savings, worst_extra_time_ratio, 0, 0, elem_high_mixed,
                new_r1, new_r2)
    #Determine by how much (if at all) the capacity constraints are violated
    #for each of the two possible assignments of the buses to the routes
    bus1_for_newr1 = r1.bus.can_handle(new_r1, True, True)
    bus2_for_newr2 = r2.bus.can_handle(new_r2, True, True)
    worst_cap_ratio_1 = max(bus1_for_newr1, bus2_for_newr2)
    bus1_for_newr2 = r1.bus.can_handle(new_r2, True, True)
    bus2_for_newr1 = r2.bus.can_handle(new_r1, True, True)
    worst_cap_ratio_2 = max(bus1_for_newr2, bus2_for_newr1)
    return (savings, worst_extra_time_ratio,
            worst_cap_ratio_1, worst_cap_ratio_2, elem_high_mixed,
            new_r1, new_r2)

def check_all_uncrossings(route_plan):
    uncrossings = []
    crossing_pairs_total = 0
    #Function to find the largest ratio of obtained value to
    #allowed value
    #note: set to 2 if elementary and high are mixed
    violation_ratio = lambda x: max(max(x[1], min(x[2], x[3])), 2*x[4])
    for (r1ind, r1) in enumerate(route_plan):
        for (r2ind, r2) in enumerate(route_plan):
            #Don't want to check crossing routes that visit
            #all different schools
            #if set(r1.schools) != set(r2.schools):
            #    continue
            if len(set(r1.schools).intersection(set(r2.schools))) == 0:
                continue
            #Don't want to duplicate work
            if r1ind <= r2ind:
                continue
            crossings = route_pair_crossings(r1, r2)
            if len(crossings) > 0:
                if r1ind == 5 and r2ind == 2:
                        print("checking this one")
                crossing_pairs_total += 1
                best_result = None
                best_i1, best_i2 = -1, -1
                for (i1, i2) in product(range(len(r1.stops) + 1), range(len(r2.stops) + 1)):
                    result = try_uncrossing(r1, r2, i1, i2)
                    if result == -1:
                        continue
                    if best_result == None or violation_ratio(result) < violation_ratio(best_result):
                        best_result = result
                        best_i1 = i1
                        best_i2 = i2
                if best_result != None:
                    uncrossings.append(((r1, r2, best_i1, best_i2), best_result))
    #Sort the results by least-violating of the constraints
    uncrossings.sort(key = lambda x: violation_ratio(x[1]))
    for uncrossing in uncrossings:
        print(uncrossing)
    print(crossing_pairs_total)
    return uncrossings
    
setup_parameters('data//parameters.csv', True)
setup_mod_caps('data//modified_capacities.csv')
    
loading = open("output//topresent0805.obj", "rb")
obj = pickle.load(loading)
final_result_allschools = check_all_uncrossings(obj)
loading.close()   