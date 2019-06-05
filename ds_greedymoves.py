import constants
import networkx as nx
import numpy as np
from ds_setup import setup_ds_stops, setup_ds_students

#Moves all stops of travel time index tt_ind from
#route1 to route2. Returns False if student types or bell times are
#incompatible, in which case both routes are restored.
#Does not enforce time limits.
def perform_move(route1, route2, tt_ind):
    #Trivial case
    if route1 == route2:
        return True
    stops_to_move = []
    for stop in route1.stops:
        if stop.tt_ind == tt_ind:
            stops_to_move.append(stop)
    #Check feasibility with respect to ages
    # for stop in stops_to_move:
    #     if (route2.e_no_h and stop.h > 0 and stop.e == 0 or
    #         route2.h_no_e and stop.e > 0 and stop.h == 0):
    #         return False
    #Now should be valid with respect to ages
    #May still be invalid with respect to school
    #bell times, in which case we restore and
    #return False
    for stop in stops_to_move:
        route1.remove_stop(stop)
        #If stop was never added, bell times failed
        route2.insert_mincost(stop)
        if stop not in route2.stops:
            route1.restore()
            route2.restore()
            return False
    return True

#Cycles through all pairs of routes to see where improvements can
#be made. Output: a list of tuples (route_from, route_to, tt_ind, feasible)
#Feasible if the route the stops are moved to is still within travel
#time limits.
#pref_modified can speed things up if you only want greedy moves
#involving a certain subset.
#If slack is positive, include moves with positive costs
def identify_greedy_moves(route_plan, subset = None, slack = 0):
    
    if subset == None:
        subset = route_plan
    all_moves = []
    for route in route_plan:
        route.backup()
    for route1 in route_plan:
        for route2 in route_plan:
            if route1 not in subset and route2 not in subset:
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
                    #if (new_r1_travel + new_r2_travel + .1 < 
                    #    original_r1_travel + original_r2_travel):
                    #    all_moves.append((route1, route2, tt_ind, feasible))
                    #if (savings + .0005*(original_r2_travel + original_r1_travel)
                    #    > costs + .0005*(new_r1_travel + new_r2_travel) + .1):
                    #    all_moves.append((route1, route2, tt_ind, feasible))
                route1.restore()
                route2.restore()
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
                print("Made a move")
                if not perform_move(move[0], move[1], move[2]):
                    print("Oops")
                modified.add(move[0])
                modified.add(move[1])
                improved = True
    print("Next iter")
    if improved: #Keep looking for improvements
        make_greedy_moves(route_plan, modified)
    #Now delete routes with no stops
    to_delete = set()
    for route in route_plan:
        if len(route.stops) == 0:
            to_delete.add(route)
    for route in to_delete:
        print("Saved one")
        route_plan.remove(route)
        
#DFS to find a single cycle which is valid in that it does
#not visit the same route twice or any of the modified routes
def find_cycle(G, current_moves, inds, modified = set(),
               cur_modified = set(), so_far = []):
    if len(so_far) > 100:
        return None
    if len(cur_modified) > 150:
        print("strange")
    if len(so_far) == 0:
        for n in G.nodes:
            if constants.VERBOSE and n % 100 == 0:
                print(n)
            #Node that has already been changed - don't try it
            if current_moves[n][0] in modified or current_moves[n][1] in modified:
                #print(str(n) + " modified " + str(current_moves[n][0]) +
                #      " " + str(current_moves[n][1]) + " " + str(len(modified)))
                continue
            new_set = set()
            new_set.add(current_moves[n][1])
            new_moves = [current_moves[n]]
            if find_cycle(G, current_moves, inds, modified = modified,
                          cur_modified = new_set, so_far = new_moves) != None:
                return new_moves
    if len(so_far) > 0:
        n = inds[so_far[-1]]
        for new_node in G.neighbors(n):
            move = current_moves[new_node]
            if move[1] not in modified and move[1] not in cur_modified:
                so_far.append(move)
                cur_modified.add(move[1])
                if find_cycle(G, current_moves, inds, modified,
                              cur_modified, so_far) != None:
                    return so_far
                del so_far[-1]
                cur_modified.remove(move[1])
            if move == so_far[0]:
                old_time = 0
                for to_check in cur_modified:
                    old_time += to_check.length
                for to_move in so_far:
                    perform_move(to_move[0], to_move[1], to_move[2])
                new_time = 0
                for to_check in cur_modified:
                    new_time += to_check.length
                if new_time < old_time - .01:      
                    for to_check in cur_modified:
                        to_check.backup()
                    return so_far
                #print("False alarm " + str(old_time - new_time))
                for to_check in cur_modified:
                    to_check.restore()
                return None
    return None


def find_greedy_cycles(route_plan):
    current_moves = identify_greedy_moves(route_plan, slack = 100)
    for route in route_plan:
        route.backup()
    
    #Dictionary from routes to indices
    inds = dict()
    for i in range(len(current_moves)):
        inds[current_moves[i]] = i
    
    #In this graph, an edge from move 1 to move 2 indicates that
    #the route in the middle remains feasible when these moves
    #are both carried out.
    G = nx.DiGraph()
    for i in range(len(current_moves)):
        G.add_node(i)
    
    if constants.VERBOSE:
        print(len(current_moves))
    counter = 0
    for move1 in current_moves:
        counter += 1
        if counter % 1000 == 0:
            print(counter)
        for move2 in current_moves:
            if move1[1] != move2[0]:  #Moves are not attached
                continue
            #In the case where both moves have the same tt_ind, might as
            #well move from the first to the third and skip the middleman.
            #This avoids issues with noncommutative moves.
            if move1[2] == move2[2]:
                continue
            perform_move(move1[0], move1[1], move1[2])
            perform_move(move2[0], move2[1], move2[2])
            if move2[0].length <= move2[0].max_time:
                G.add_edge(inds[move1], inds[move2])
            move1[0].restore()
            move1[1].restore()
            move2[1].restore()
    if constants.VERBOSE:
        print(nx.number_of_edges(G))
        print("Done evaluating moves")

    modified = set()
    improved = False
    while True:
        result = find_cycle(G, current_moves, inds, modified = modified)
        if result != None:
            improved = True
            if constants.VERBOSE:
                print("Found an improvement of length " + str(len(result)))
                print("Total length: " + str(np.sum(np.array([r.length for r in route_plan]))))
            for move in result:
                modified.add(move[0])
            print(len(modified))
        else:
            break
    if improved:
        find_greedy_cycles(route_plan)
          
# import pickle as pickle
# #Determine whether to actually run anything or just import functions
# running = False
# if running:
#     loading = open(("output//8minutesdropoff.obj"), "rb")
#     routes = pickle.load(loading)
#     loading.close()
#     print("Original number of routes is " + str(len(routes)))
#     print("Original total travel time is " + str(sum([sum(r.student_travel_times()) for r in routes])))
#     make_greedy_moves(routes)
#     #constants.MAX_TIME = 3600
#     for route in routes:
#         route.recompute_maxtime()
#     print("New number of routes is " + str(len(routes)))
#     print("New total travel time is " + str(sum([sum(r.student_travel_times()) for r in routes])))
#     saving = open(("output//8minutesdropoffgreedy.obj"), "wb")
#     pickle.dump(routes, saving)
#     saving.close()
        
#     cap_counts = setup_buses('data//dist_bus_capacities.csv')
#     result = assign_buses(routes, cap_counts)
#     saving = open(("output//8minutesdropoffgreedyb.obj"), "wb")
#     pickle.dump(result, saving)
#     saving.close()
#     print("Number of bused routes is " + str(len(result)))
