import constants
from locations import School, Stop
from route import Route
from random import shuffle

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
        
def generate_routes(schools):
    all_stops = []
    for school in schools:
        all_stops.extend(school.unrouted_stops['E'])
        all_stops.extend(school.unrouted_stops['M'])
        all_stops.extend(school.unrouted_stops['H'])
    #We will process the stops in order of distance
    #from their schools - an "inward-out" approach.
    #683 unbused routes given 45 minutes
    all_stops = sorted(all_stops, key = lambda s: trav_time(s, s.school))
    #Trying other things...
    #all_stops = sorted(all_stops, key = lambda s: (len(s.school.unrouted_stops['E'])+len(s.school.unrouted_stops['M'])+len(s.school.unrouted_stops['H'])))
    routes = set()
    near_schools = determine_school_proximities(schools)
    while len(all_stops) > 0:
        print(len(all_stops))
        current_route = Route()
        #Pick up the most distant stop
        init_stop = all_stops[0]
        root_school = init_stop.school
        #Figure out which schools can be mixed with the stop
        admissible_schools = near_schools[root_school]
        current_route.add_stop(init_stop)
        #Now we will try to add a stop
        while True:
            oldlength = current_route.length
            current_route.backup()
            best_score = 100000
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
                        dist = trav_time(stop, stop.school)
                        score = time_cost / dist
                        if score < best_score:
                            best_score = score
                            best_stop = stop
                    current_route.restore()
            if best_stop == None:
                break
            current_route.insert_mincost(best_stop)
            best_stop.school.unrouted_stops[init_stop.type].remove(best_stop)
            all_stops.remove(best_stop)
        print(len(current_route.stops))
        routes.add(current_route)
    return routes