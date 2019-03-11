import constants
from locations import Student, School

def searchgreedy(routes):
    changed = True
    while changed:
        changed = False
        for route_to in routes:
            print("Next")
            for route_from in routes:
                oldsum = route_to.length + route_from.length
                locs = route_from.locations
                route_to.backup()
                route_from.backup()
                for i in range(len(locs)):
                    if i >= len(locs):
                        break
                    if isinstance(locs[i], School):
                        continue
                    if (i == 0 or
                        isinstance(locs[i-1], School) or
                        locs[i-1].tt_ind != locs[i].tt_ind or
                        locs[i-1].school != locs[i].school):
                        if (route_from.remove_and_add(i, route_to) and
                            route_from.length + route_to.length < oldsum):
                            print("Found an improvement of " +
                                  str(-route_from.length - route_to.length + oldsum))
                            changed = True
                            oldsum = route_from.length + route_to.length
                            route_to.backup()
                            route_from.backup()
                            locs = route_from.locations
                        else:
                            route_to.restore()
                            route_from.restore()
                        
                        