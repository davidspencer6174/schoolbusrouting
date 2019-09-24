import constants
import itertools
import numpy as np

def write_output(students_filename, output_filename, route_plan):
    from diagnostics import google_maps_strings
    print("Saving data...")
    
    to_save = open(output_filename, 'w')
    student_records = open(students_filename, 'r')
    
    lines = []
    header_line = student_records.readline().replace(",", "\t").strip()  #header
    header_line += "\tStudent ID\tRoute number\tSchool name\tBus capacity\tRoute occupants\tStop occupants\tGoogle Maps link"
    lines.append(header_line)
    for student_record in student_records.readlines():
        student_record = student_record.replace(",", "\t").strip()
        lines.append(student_record)
    for (route_num, route) in enumerate(route_plan):
        for stop in route.stops:
            for stud in stop.students:
                ind = stud.file_index
                lines[ind] += "\t" + str(stud.student_id_number)
                lines[ind] += "\t" + str(route_num)
                lines[ind] += "\t" + str(stud.school.school_name)
                lines[ind] += "\t"
                if route.bus != None:
                    lines[ind] += str(route.bus.capacity)
                lines[ind] += "\t" + str(route.occupants)
                occs_at_stop = 0
                for stop2 in route.stops:
                    if stop2.tt_ind == stop.tt_ind:
                        occs_at_stop += stop2.occs
                lines[ind] += "\t" + str(occs_at_stop)
                lines[ind] += "\t"
                for link in google_maps_strings(route):
                    lines[ind] += link + " "
                lines[ind] = lines[ind].strip()
    for line in lines:
        to_save.write(line + "\n")
    to_save.close()
    print("Done saving data.")
    

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

#Checks if two stop objects are isomorphic, even if they are
#not the same object in memory.
def isomorphic(stop1, stop2):
    return(stop1.school.tt_ind == stop2.school.tt_ind and
           stop1.tt_ind == stop2.tt_ind)

#Returns a set of tuples
#(s1.tt_ind, s1.school.tt_ind, s2.tt_ind, s2.school.tt_ind)
#containing all stops for which s1 and s2 are in the same route.
#Note: there will be double-counting due to swapping s1 and s2.
def stop_pairs(route_plan):
    out = set()
    for r in route_plan:
        for stop1 in r.stops:
            for stop2 in r.stops:
                if stop1 == stop2:
                    continue
                out.add((stop1.tt_ind, stop1.school.tt_ind,
                         stop2.tt_ind, stop2.school.tt_ind))
    return out

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

#A route in rp1 shares an edge with a route in rp2 if they
#pick up at least one common student. The common stop
#similarity is defined to be max(len(rp1, rp2))/(total # edges).
def common_stop_similarity(rp1, rp2):
    num_edges = 0
    for r in rp1:
        overlaps = overlapping_routes(rp2, r)
        num_edges += len(overlaps)
    return max(len(rp1), len(rp2))/(num_edges)

#For each route plan, construct the stop_pairs object as
#defined by that function.
#Then compute the overlap between these sets of pairs using
#|intersection|/|union|.
def common_stop_pairs(rp1, rp2):
    rp1pairs = stop_pairs(rp1)
    rp2pairs = stop_pairs(rp2)
    return len(rp1pairs.intersection(rp2pairs))/len(rp1pairs.union(rp2pairs))

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
    print(str(tot) + " routes appear in both route plans.")
    print("Number of stops in these common routes:")
    iso_stops_same.sort()
    print(iso_stops_same)
    
def two_opt(route):
    num_stops = len(route.stops)
    orig_length = route.length
    for ind1 in range(num_stops):
        for ind2 in range(ind1+2, num_stops):
            route.stops[ind1:ind2] = route.stops[ind1:ind2][::-1]
            route.recompute_length()
            if route.length < orig_length and route.feasibility_check():
                if constants.VERBOSE:
                    print("Improved")
                two_opt(route)
                return
            route.stops[ind1:ind2] = route.stops[ind1:ind2][::-1]
    route.recompute_length()
          
#Determines mean student travel time
def mstt(route_plan):
    trav_times = []
    for route in route_plan:
        trav_times.extend(route.student_travel_times())
    trav_times = np.array(trav_times)
    return np.mean(trav_times)
    
#Entries in to_do determine whether we make greedy moves, do two_opt,
#and do Park/Kim's mixed-load procedure.
#route_plan should be a list.
def improvement_procedures(route_plan, to_do = [True, True, True]):
    from greedymoves import make_greedy_moves
    from mixedloads import mixed_loads
    while True:
        prev_num_routes = len(route_plan)
        prev_mean_trav = mstt(route_plan)
        if to_do[0]:
            make_greedy_moves(route_plan)
            for route in route_plan:
                assert route.feasibility_check(verbose = True)
        if to_do[1]:
            for route in route_plan:
                two_opt(route)
            for route in route_plan:
                assert route.feasibility_check(verbose = True)
        if to_do[2]:
            mixed_loads(route_plan)
            for route in route_plan:
                assert route.feasibility_check(verbose = True)
        if (len(route_plan) == prev_num_routes and
            mstt(route_plan) == prev_mean_trav):
            break
    return route_plan