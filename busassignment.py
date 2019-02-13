import constants

#routes is any iterable of the routes we want to assign
#buses is a list of lists of length 2 [capacity, count]
#the buses will be modified to whichever buses remain
#after the assignment
#the routes list will be sorted
#TODO: Actually build the resulting routes, since
#routes may need to be split
#TODO: Implement use of contract buses

def assign_buses(routes, buses):
    routes = sorted(routes, key = lambda r:r.occupants)
    buses = sorted(buses, key = lambda b:b[0])
    cap_map = constants.CAPACITY_MODIFIED_MAP
    
    consumed = 0
    for r in routes:
        occs = r.occupants
        #Only handles elementary, middle, high
        type_ind = constants.TYPE_IND_MAP[r.locations[0].type]
        #Keep assigning buses until there are no students left.
        #Use the smallest possible bus
        while occs > 0:
            bus_used = None
            for b in buses:
                if cap_map[b[0]][type_ind] >= occs:
                    occs = 0
                    b[1] -= 1
                    bus_used = b
                    consumed += 1
                    break
            #Nothing large enough for all - take as many as possible
            if bus_used == None:
                bus_used = buses[-1]
                occs -= bus_used[0]
                bus_used[1] -= 1
                consumed += 1
            #if we've used the last bus, get it out of the list
            if bus_used[1] == 0:
                buses.remove(bus_used)
    return consumed
        