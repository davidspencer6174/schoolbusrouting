import constants

def make_greedy_moves(route_plan):
    improved = False
    for route1 in route_plan:
        route1.backup()
        tt_inds = set()
        for stop in route1.stops:
            tt_inds.add(stop.tt_ind)
        if len(route1.stops) == 0:
            continue
        route1_type = route1.stops[0].type
        for tt_ind in tt_inds:
            oldtime1 = route1.length
            stops_to_move = set()
            for stop in route1.stops:
                if stop.tt_ind == tt_ind:
                    stops_to_move.add(stop)
            for stop in stops_to_move:
                route1.remove_stop(stop)
            savings = oldtime1 - route1.length
            this_improved = False
            for route2 in route_plan:
                if len(route2.stops) == 0:
                    continue
                if route2.stops[0].type != route1_type:
                    continue
                if route2 == route1:
                    continue
                route2.backup()
                oldtime2 = route2.length
                feasible = True
                for stop in stops_to_move:
                    if not route2.insert_mincost(stop):
                        feasible = False
                        break
                cost = route2.length - oldtime2
                if savings > cost and feasible:
                    if constants.VERBOSE:
                        print("Saved " + str(savings-cost))
                    improved = True
                    this_improved = True
                    route1.backup()
                    break
                else:
                    route2.restore()
            if not this_improved:
                route1.restore()
    if improved:
        make_greedy_moves(route_plan)
    to_delete = set()
    for route in route_plan:
        if len(route.stops) == 0:
            to_delete.add(route)
    for route in to_delete:
        print("Saved one")
        route_plan.remove(route)