import constants
import itertools
import numpy as np
from diagnostics import printout, printout_google_maps

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
            if (constants.TRAVEL_TIMES[from_loc.tt_ind,
                                       to_loc.tt_ind] < opt_dist and
                (age_type == None or to_loc.type == age_type)):
                opt_dist = constants.TRAVEL_TIMES[from_loc.tt_ind,
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
            if ((constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                (constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha) < opt_cost and
                constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < available_time and
                (age_type == None or loc.type == age_type)):
            #if (constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
            #    constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
            #    constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind] < opt_dist and
            #    (age_type == None or loc.type == age_type)):
                opt_cost = ((constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                           constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])/
                            (constants.TRAVEL_TIMES[loc.tt_ind, loc.school.tt_ind]**alpha))
                opt_dist = (constants.TRAVEL_TIMES[locations[i].tt_ind, loc.tt_ind] +
                            constants.TRAVEL_TIMES[loc.tt_ind, locations[i+1].tt_ind] -
                            constants.TRAVEL_TIMES[locations[i].tt_ind, locations[i+1].tt_ind])
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

#Checks to see which routes in the first route plan share at least
#one stop with the passed-in route.
#Does not require pointer equality for stops, only object value
#equality.
def overlapping_routes(route_plan, route):
    out = set()
    for compare_route in route_plan:
        for stop1 in compare_route.stops:
            for stop2 in route.stops:
                if isomorphic(stop1, stop2):
                    out.add(compare_route)
    return out

def full_comparison(rp1, rp2):
    tot = 0
    for r in rp1:
        out = overlapping_routes(rp2, r)
        if len(out) == 1:
            tot += 1
    print("Route Plan 2 has " + str(tot) + " routes that are subroutes "+
          "of routes in Route Plan 1.")
    tot = 0
    for r in rp2:
        out = overlapping_routes(rp1, r)
        if len(out) == 1:
            tot += 1
    print("Route Plan 1 has " + str(tot) + " routes that are subroutes "+
          "of routes in Route Plan 2.")
    tot = 0
    iso_stops_same = []
    for r in rp1:
        out = overlapping_routes(rp2, r)
        if len(out) == 1:
            r2 = list(out)[0]
            out2 = overlapping_routes(rp1, r2)
            if len(out2) == 1:
                r1 = list(out)[0]
                tot += 1
                stop_inds = set()
                for stop in r2.stops:
                    stop_inds.add(stop.tt_ind)
                iso_stops_same.append(len(stop_inds))
                if len(stop_inds) == 5: #what is happening here?
                    for stop in r1.stops:
                        if stop.school.school_name == None:
                            print(stop.occs)
                    for stop in r2.stops:
                        print(stop.occs)
                    print(r1.stops)
                    print(r2.stops)
                    #printout_google_maps(r1)
                    #printout_google_maps(r2)
    print(str(tot) + " routes appear in both route plans.")
    print("Number of stops in these common routes:")
    iso_stops_same.sort()
    print(iso_stops_same)