import constants
import networkx as nx
import numpy as np
from setup import setup_buses, setup_stops, setup_students
from busassignment_bruteforce import assign_buses

#Moves all stops of travel time index tt_ind from
#route1 to route2. Returns False if the move is not valid,
#in which case both routes are restored.
def perform_move(route1, route2, tt_ind):
    #Trivial case
    if route1 == route2:
        return True
    stops_to_move = []
    for stop in route1.stops:
        if stop.tt_ind == tt_ind:
            stops_to_move.append(stop)
    #Check feasibility with respect to ages
    for stop in stops_to_move:
        if (route2.e_no_h and stop.h > 0 and stop.e == 0 or
            route2.h_no_e and stop.e > 0 and stop.h == 0):
            return False
    #Now should be valid with respect to ages
    #May still be invalid with respect to school
    #bell times, in which case we restore and
    #return False
    for stop in stops_to_move:
        route1.remove_stop(stop)
        #If stop was never added, bell times failed
        route2.insert_mincost(stop)
        if stop not in route2.stops:
            route1.restore("identify_greedy_moves")
            route2.restore("identify_greedy_moves")
            return False
    return True

#Cycles through all pairs of routes to see where improvements can
#be made. Output: a list of tuples (route_from, route_to, tt_ind, feasible)
#Feasible if the route the stops are moved to is still within travel
#time limits.
#pref_modified can speed things up if you only want greedy moves
#involving a certain subset.
#If slack is positive, include moves with positive costs
def identify_greedy_moves(route_plan, subset = None, slack = -1):
    
    if subset == None:
        subset = route_plan
    all_moves = []
    for route in route_plan:
        route.backup("identify_greedy_moves")
    for route1 in route_plan:
        for route2 in route_plan:
            if route1 not in subset and route2 not in subset:
                continue
            if (len(route1.special_ed_students) +
                len(route2.special_ed_students)) > 0 and route1.schools != route2.schools:
                continue
            if len(route1.stops) == 0 or len(route2.stops) == 0: #No longer exists
                continue
            original_r1_length = route1.length
            original_r2_length = route2.length
            #original_r1_travel = sum(route1.student_travel_times())
            #original_r2_travel = sum(route2.student_travel_times())
            tt_inds = []
            for stop in route1.stops:
                tt_inds.append(stop.tt_ind)
            for tt_ind in tt_inds:
                if perform_move(route1, route2, tt_ind):
                    savings = original_r1_length - route1.length
                    costs = route2.length - original_r2_length
                    #new_r1_travel = sum(route1.student_travel_times())
                    #new_r2_travel = sum(route2.student_travel_times())
                    feasible = (route1.length < route1.max_time and
                                route2.length < route2.max_time)
                    if savings + slack > costs:
                        #Append a description of this move
                        all_moves.append((route1, route2, tt_ind, feasible, savings, costs))
                route1.restore("identify_greedy_moves")
                route2.restore("identify_greedy_moves")
    return all_moves

#Simple approach to make all of the greedy moves given as
#feasible by identify_greedy_moves.
def make_greedy_moves(route_plan, subset = None):
    if subset == None:
        subset = route_plan
    improved = False
    possible_moves = identify_greedy_moves(route_plan, subset)
    modified = set() #Track which ones we've modified to keep from
    #breaking a route by adding too much to it
    for move in possible_moves:
        if move[3]: #Feasible move
            if move[0] not in modified and move[1] not in modified:
                assert perform_move(move[0], move[1], move[2])
                modified.add(move[0])
                modified.add(move[1])
                improved = True
    if improved: #Keep looking for improvements
        make_greedy_moves(route_plan, modified)
    #Now delete routes with no stops
    to_delete = set()
    for route in route_plan:
        if len(route.stops) == 0:
            to_delete.add(route)
    for route in to_delete:
        route_plan.remove(route)