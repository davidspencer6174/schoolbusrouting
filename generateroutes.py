import constants
from locations import School, Stop
from route import Route
from random import random, shuffle, randint

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

#Returns a dictionary from Schools to sets of
#Schools, where the set of Schools consists of
#all schools within MAX_SCHOOL_DIST seconds of the input
#school.
def determine_school_proximities(schools):
    near_schools = dict()
    for school1 in schools:
        near_schools[school1] = set()
        for school2 in schools:
            if ((trav_time(school1, school2) <= constants.MAX_SCHOOL_DIST) and
                (school1.school_name, school2.school_name) not in constants.FORBIDDEN_SCHOOL_PAIRS):
                near_schools[school1].add(school2)
            if (school1.school_name, school2.school_name) in constants.ALLOWED_SCHOOL_PAIRS:
                near_schools[school1].add(school2)
    return near_schools

def apply_partial_route_plan(partial_route_plan, all_stops, new_route_plan):
    for route in partial_route_plan:
        new_route = Route()
        new_route_plan.add(new_route)
        for stop in route.stops:
            isomorphic_stop = None
            for search_stop in all_stops:
                if (search_stop.school.school_name == stop.school.school_name and
                    search_stop.tt_ind == stop.tt_ind):
                    isomorphic_stop = search_stop
                    break
            if isomorphic_stop == None:
                print("Stop not found")
            new_route.add_stop(isomorphic_stop)
            isomorphic_stop.school.unrouted_stops.remove(isomorphic_stop)
            all_stops.remove(isomorphic_stop)
            for stop in isomorphic_stop.school.unrouted_stops:
                stop.update_value(isomorphic_stop)
    print("Done applying partial route plan")
            
        
def generate_routes(schools, permutation = None, partial_route_plan = None, sped = False):
    all_stops = []
    for school in schools:
        all_stops.extend(school.unrouted_stops)
    #Initialize stop values
    for stop in all_stops:
        stop.update_value(None)
    #We will process the stops in order of distance
    #from their schools
    #The second and part of the tuple improves
    #determinism of the sorting algorithm.
    all_stops = sorted(all_stops, key = lambda s: (-trav_time(s, s.school),
                                                   s.school.school_name))
    if len(all_stops) == 0:
        return []
    if permutation != None:
        all_stops = [all_stops[i] for i in permutation]
    routes = []
    near_schools = determine_school_proximities(schools)
    if partial_route_plan != None:
        apply_partial_route_plan(partial_route_plan, all_stops, routes)
    while len(all_stops) > 0:
        current_route = Route()
        #Pick up the most distant stop
        init_stop = all_stops[0]
        root_school = init_stop.school
        root_school.unrouted_stops.remove(init_stop)
        all_stops.remove(init_stop)
        #Figure out which schools can be mixed with the stop
        admissible_schools = near_schools[root_school]
        if sped: #special ed: no mixed load routing
            admissible_schools = set([root_school])
        current_route.add_stop(init_stop)
        e_no_h = False
        h_no_e = False
        if init_stop.e > 0 and init_stop.h == 0:
            e_no_h = True
        if init_stop.h > 0 and init_stop.e == 0:
            h_no_e = True
        #Now we will try to add a stop
        
        while True:
            oldlength = current_route.length
            current_route.backup("generation")
            #best_score = -100000
            best_score = constants.EVALUATION_CUTOFF
            best_stop = None
            
            for school in admissible_schools:
                for stop in school.unrouted_stops:
                    #Not feasibile with respect to age types
                    if (e_no_h and stop.h > 0 and stop.e == 0 or
                        h_no_e and stop.e > 0 and stop.h == 0):
                        continue
                    if current_route.insert_mincost(stop):
                        #Stop was successfully inserted.
                        #Determine the score of the stop
                        #We want to penalize large time
                        #increases while rewarding collecting
                        #faraway stops.
                        time_cost = current_route.length - oldlength
                        value = stop.value
                        score = value - time_cost
                        
                        #stop in the same place, but different age
                        if time_cost == 0:
                            score = 100000
                        if score > best_score:
                            best_score = score
                            best_stop = stop
                        current_route.restore("generation")
            if best_stop == None:
                break
            msg = "Failed to insert stop after insertion was verified"
            assert current_route.insert_mincost(best_stop), msg
            best_stop.school.unrouted_stops.remove(best_stop)
            all_stops.remove(best_stop)
            for stop in best_stop.school.unrouted_stops:
                stop.update_value(best_stop)
            if best_stop.e > 0 and best_stop.h == 0:
                e_no_h = True
            if best_stop.h > 0 and best_stop.e == 0:
                h_no_e = True
        routes.append(current_route)
    return list(routes)