import constants
import copy
import itertools
from locations import School, Stop, Student

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

class Route:
    
    #Encapsulated as a list of Stops in order and
    #a list of Schools in order.
    #It is assumed that the Schools are all visited
    #after the Stops.
    def __init__(self):
        self.stops = []
        self.schools = []
        self.length = 0
        self.occupants = 0
        self.valid_school_orderings = []
        self.max_time = constants.MAX_TIME
        #If no bus is assigned, the default capacity is infinite.
        #This is denoted by a -1.
        #Otherwise, this variable should be modified to reflect
        #the actual capacity.
        self.unmodified_bus_capacity = -1
        self.bus_capacity = -1
        
    #This is a backup used during the mixed-load post improvement
    #procedure when it is determined that a bus cannot be deleted,
    #and so all routes must be reverted and the moved students
    #returned to the bus.    
    def backup(self):
        self.backup_stops = copy.copy(self.stops)
        self.backup_schools = copy.copy(self.schools)
        self.backup_occs = self.occupants
        self.backup_length = self.length
        self.backup_max_time = self.max_time
        self.backup_school_orderings = copy.copy(self.valid_school_orderings)
        
    def restore(self):
        self.stops = copy.copy(self.backup_stops)
        self.schools = copy.copy(self.backup_schools)
        self.occupants = self.backup_occs
        self.length = self.backup_length
        self.max_time = self.backup_max_time
        self.valid_school_orderings = copy.copy(self.backup_school_orderings)
        
    #Inserts a stop visit at position pos in the route.
    #The default position is the end.
    #Does not do any checks.
    def add_stop(self, stop, pos = -1):
        if not self.add_school(stop.school):
            return False
        if pos == -1:
            self.stops.append(stop)
            #Maintain the travel time field and occupants field
            self.occupants += stop.occs
            self.recompute_length()
            return
        #Add the stop
        self.stops = self.stops[:pos] + [stop] + self.stops[pos:]
        #Maintain the travel time field and occupants field
        #TODO: memoize length for cheaper maintenance
        self.recompute_length()
        self.occupants += stop.occs
        self.max_time = max(self.max_time,
                            constants.SLACK*trav_time(stop, stop.school))
        
    def get_route_length(self):
        return self.length
    
    #Performs an insertion of a stop such that the cost is minimized.
    #TODO: Allow for addition to the end to interface with
    #reorderings of the schools
    def insert_mincost(self, stop):
        if not self.add_school(stop.school):
            return False
        best_cost = 100000
        best_ind = 0
        if len(self.stops) > 0:
            best_cost = trav_time(stop, self.stops[0])
            for i in range(len(self.stops) - 1):
                cost = (trav_time(self.stops[i], stop)
                        + trav_time(stop, self.stops[i + 1])
                        - trav_time(self.stops[i], self.stops[i + 1]))
                if cost < best_cost:
                    best_cost = cost
                    best_ind = i + 1
        final_cost = (trav_time(self.stops[-1], stop) +
                      trav_time(stop, self.schools[0]))
        if final_cost < best_cost:
            self.stops.append(stop)
        else:
            self.stops.insert(best_ind, stop)
        self.recompute_length()
        self.occupants += stop.occs
        self.max_time = max(self.max_time,
                            constants.SLACK*trav_time(stop, stop.school))
        return (self.length <= self.max_time)
    
    #Checks whether adding the school would leave
    #any valid orderings. If so, adds the school
    #and returns True.
    def add_school(self, school):
        if school not in self.schools:
            self.schools.append(school)
            self.enumerate_school_orderings()
            if len(self.valid_school_orderings) == 0:
                self.schools.remove(school)
                self.enumerate_school_orderings()
                return False
        return True
        
    
    #Outputs (valid, time) where valid is true if the belltimes
    #line up appropriately and time gives the amount of time
    #required to use this ordering.
    def time_check(self, school_perm):
        time = 0
        mintime = school_perm[0].start_time - constants.EARLIEST
        maxtime = school_perm[0].start_time - constants.LATEST
        for i in range(1, len(school_perm)):
            leg_time = trav_time(school_perm[i-1], school_perm[i])
            mintime += trav_time(school_perm[i-1], school_perm[i])
            maxtime += trav_time(school_perm[i-1], school_perm[i])
            time += leg_time
            school_mintime = school_perm[i].start_time - constants.EARLIEST
            school_maxtime = school_perm[i].start_time - constants.LATEST
            #Can't get to the school in time - give up
            if school_maxtime < mintime:
                return (False, 0)
            #Have to wait at the school - add the waiting time
            if school_mintime > maxtime:
                time += school_mintime - maxtime
            mintime = max(school_mintime, mintime)
            maxtime = min(school_maxtime, max(maxtime, mintime))
        return (True, time)
    
    def enumerate_school_orderings(self):
        self.valid_school_orderings = []
        for perm in itertools.permutations(self.schools):
            result = self.time_check(perm)
            if result[0]:
                self.valid_school_orderings.append([list(perm), result[1]])
        
    #If there is ever uncertainty about the length field, recompute length
    def recompute_length(self):
        length = 0
        for i in range(len(self.stops) - 1):
            length += trav_time(self.stops[i], self.stops[i+1])
        best_length = 100000
        for possible_schools in self.valid_school_orderings:
            #Length is stop travel time plus stop to first school
            #plus school travel time
            possible_length = (length +
                               trav_time(self.stops[-1], possible_schools[0][0]) +
                               possible_schools[1])
            if possible_length < best_length:
                best_length = possible_length
                self.schools = possible_schools[0]
        self.length = best_length
        return best_length
        
    #Determines whether the route is feasible with
    #respect to constraints.
    #Simple for now
    def feasibility_check(self, verbose = False):
        #Too long
        if self.length > self.max_time:
            if verbose:
                print("Too long")
            return False
        #Too many students and there is a bus assigned
        if self.bus_capacity > -1 and self.occupants > self.bus_capacity:
            if verbose:
                print("Too full")
            return False
        #Now test mixed load bell time feasibility
        result = self.time_check(self.schools)
        if not result[0]:
            print("Bell times contradict")
            return False
        return True
    
    #Given a capacity, checks the age of the student and
    #stores the corresponding capacity
    def set_capacity(self, cap):
        self.unmodified_bus_capacity = cap
        first_stud = None
        for loc in self.locations:
            if isinstance(loc, Student):
                first_stud = loc
                break
        if first_stud.type == 'E':
            self.bus_capacity =  constants.CAPACITY_MODIFIED_MAP[cap][0]
        elif first_stud.type == 'M':
            self.bus_capacity =  constants.CAPACITY_MODIFIED_MAP[cap][1]
        else:
            self.bus_capacity =  constants.CAPACITY_MODIFIED_MAP[cap][2]
    
    #Accepts a bus array of length 3
    #The first number is the allowable number of elementary students
    #to assign, then  middle, then high
    #Returns whether it is valid to assign the bus to the route
    def is_acceptable(self, cap):
        if self.locations[0].type == 'E':
            return constants.CAPACITY_MODIFIED_MAP[cap][0] >= self.occupants
        elif self.locations[0].type == 'M':
            return constants.CAPACITY_MODIFIED_MAP[cap][1] >= self.occupants
        else:
            return constants.CAPACITY_MODIFIED_MAP[cap][2] >= self.occupants
    
    #Check whether it is feasible to add more students to the route
    #given the bus capacity
    def can_add(self, cap, num_students = 1):
        self.occupants += num_students
        out = self.is_acceptable(cap)
        self.occupants -= num_students
        return out