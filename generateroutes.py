import constants
from locations import School, Stop
from route import Route
from random import random, shuffle, randint

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

#Checks whether two schools have any students at all who
#are the same age type
def compatible_types(school1, school2):
    return ((len(school1.unrouted_stops['E']) > 0 and 
             len(school2.unrouted_stops['E']) > 0 ) or
             (len(school1.unrouted_stops['M']) > 0 and 
             len(school2.unrouted_stops['M']) > 0 ) or
              (len(school1.unrouted_stops['H']) > 0 and 
             len(school2.unrouted_stops['H']) > 0 ))

#Returns a dictionary from Schools to sets of
#Schools, where the set of Schools consists of
#all schools within MAX_SCHOOL_DIST minutes of the input
#school.
def determine_school_proximities(schools):
    near_schools = dict()
    for school1 in schools:
        near_schools[school1] = set()
        for school2 in schools:
            if (trav_time(school1, school2) <= constants.MAX_SCHOOL_DIST and
                compatible_types(school1, school2)):
                near_schools[school1].add(school2)
    return near_schools

def apply_partial_route_plan(partial_route_plan, all_stops, new_route_plan):
    for route in partial_route_plan:
        new_route = Route()
        new_route_plan.add(new_route)
        for stop in route.stops:
            isomorphic_stop = None
            for search_stop in all_stops:
                if (search_stop.type == stop.type and
                    search_stop.school.school_name == stop.school.school_name and
                    search_stop.tt_ind == stop.tt_ind):
                    isomorphic_stop = search_stop
                    break
            if isomorphic_stop == None:
                print("Stop not found")
            new_route.add_stop(isomorphic_stop)
            isomorphic_stop.school.unrouted_stops[isomorphic_stop.type].remove(isomorphic_stop)
            all_stops.remove(isomorphic_stop)
            for stop in isomorphic_stop.school.unrouted_stops[isomorphic_stop.type]:
                stop.update_value(isomorphic_stop)
    print("Done applying partial route plan")
            
        
def generate_routes(schools, permutation = None, partial_route_plan = None):
    all_stops = []
    for school in schools:
        all_stops.extend(school.unrouted_stops['E'])
        all_stops.extend(school.unrouted_stops['M'])
        all_stops.extend(school.unrouted_stops['H'])
    #Initialize stop values
    for stop in all_stops:
        stop.update_value(None)
    #We will process the stops in order of distance
    #from their schools
    #The second and third parts of the tuple improve
    #determinizm of the sorting algorithm.
    all_stops = sorted(all_stops, key = lambda s: (-trav_time(s, s.school),
                                                   s.type,
                                                   s.school.school_name))
    if permutation != None:
        all_stops = [all_stops[i] for i in permutation]
    #Trying other things...
#    all_stops = sorted(all_stops, key = lambda s: s.value)
#    for swap in range(20):
#        ind1 = randint(0, len(all_stops) - 1)
#        ind2 = randint(0, len(all_stops) - 1)
#        all_stops[ind1], all_stops[ind2] = all_stops[ind2], all_stops[ind1]
#    #all_stops = sorted(all_stops, key = lambda s: (len(s.school.unrouted_stops['E'])+len(s.school.unrouted_stops['M'])+len(s.school.unrouted_stops['H'])))
    routes = set()
    near_schools = determine_school_proximities(schools)
    if partial_route_plan != None:
        apply_partial_route_plan(partial_route_plan, all_stops, routes)
        #all_stops = sorted(all_stops, key = lambda s: trav_time(s, s.school))
        #all_stops = sorted(all_stops, key = lambda s: s.value)
        #for swap in range(20):
        #    ind1 = randint(0, len(all_stops) - 1)
        #    ind2 = randint(0, len(all_stops) - 1)
        #    all_stops[ind1], all_stops[ind2] = all_stops[ind2], all_stops[ind1]
    while len(all_stops) > 0:
        if constants.VERBOSE:
            print(len(all_stops))
        current_route = Route()
        #Pick up the most distant stop
        init_stop = all_stops[0]
        root_school = init_stop.school
        root_school.unrouted_stops[init_stop.type].remove(init_stop)
        all_stops.remove(init_stop)
        #Figure out which schools can be mixed with the stop
        admissible_schools = near_schools[root_school]
        current_route.add_stop(init_stop)
        #Now we will try to add a stop
        while True:
            oldlength = current_route.length
            current_route.backup()
            #best_score = -100000
            best_score = constants.EVALUATION_CUTOFF
            best_stop = None
            for school in admissible_schools:
                for stop in school.unrouted_stops[init_stop.type]:
                    if current_route.insert_mincost(stop):
                        #Stop was successfully inserted.
                        #Determine the score of the stop
                        #We want to penalize large time
                        #increases while rewarding collecting
                        #faraway stops.
                        time_cost = current_route.length - oldlength
                        value = stop.value
                        #time_proportion_left = 1 - (time_cost/(current_route.max_time - oldlength))
                        #score = value/(time_cost**1.2)
                        #score = value*(time_proportion_left+.4)
                        score = value - time_cost
                        if score > best_score:
                            best_score = score
                            best_stop = stop
                    current_route.restore()
            if best_stop == None:
                break
            if not current_route.insert_mincost(best_stop):
                print("Something went wrong")
            best_stop.school.unrouted_stops[init_stop.type].remove(best_stop)
            all_stops.remove(best_stop)
            for stop in best_stop.school.unrouted_stops[best_stop.type]:
                stop.update_value(best_stop)
        #print(len(current_route.stops))
        routes.add(current_route)
    return routes