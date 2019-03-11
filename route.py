import constants
import copy
from locations import School, Student

class Route:
    
    #Encapsulated as a list of Locations in order.
    def __init__(self):
        self.locations = []
        self.length = 0
        self.occupants = 0
        self.backup_locs = []
        self.backup_occs = 0
        self.max_time = constants.MAX_TIME
        self.backup_max_time = constants.MAX_TIME
        self.temp_backup_max_time = constants.MAX_TIME
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
        self.backup_locs = copy.copy(self.locations)
        self.backup_occs = self.occupants
        self.backup_length = self.length
        self.backup_max_time = self.max_time
        
    def restore(self):
        self.locations = self.backup_locs
        self.occupants = self.backup_occs
        self.length = self.backup_length
        self.max_time = self.backup_max_time
        
    #This is a backup used when attempting to add a single student
    #to a route. A backup will be made, the route will be modified
    #to add the student, the feasibility check will be performed,
    #and if the modified route is infeasible, the change will be reverted.
    def temp_backup(self):
        self.temp_backup_locs = copy.copy(self.locations)
        self.temp_backup_occs = self.occupants
        self.temp_backup_length = self.length
        self.temp_backup_max_time = self.max_time
        
    def temp_restore(self):
        self.locations = self.temp_backup_locs
        self.occupants = self.temp_backup_occs
        self.length = self.temp_backup_length
        self.max_time = self.temp_backup_max_time
        
    #Inserts a Location visit at position pos in the route.
    #The default position is the end.
    #Does not do any checks.
    def add_location(self, location, pos = -1):
        if pos == -1:
            self.locations.append(location)
            if len(self.locations) > 1:
                self.length += constants.TRAVEL_TIMES[self.locations[-2].tt_ind,
                                                      self.locations[-1].tt_ind]
            if isinstance(location, Student):
                self.occupants += 1
            return
        #Add the location
        self.locations = self.locations[:pos] + [location] + self.locations[pos:]
        #Maintain the travel time field
        if (pos == -1 and len(self.locations) > 1) or pos > 0:
            self.length += constants.TRAVEL_TIMES[self.locations[pos - 1].tt_ind,
                                                  self.locations[pos].tt_ind]
        if pos > -1 and pos < len(self.locations) - 1:
            self.length += constants.TRAVEL_TIMES[self.locations[pos].tt_ind,
                                                  self.locations[pos + 1].tt_ind]
        #Maintain the occupants field
        if isinstance(location, Student):
            self.occupants += 1
            self.max_time = max(self.max_time,
                                constants.SLACK*constants.TRAVEL_TIMES[location.tt_ind,
                                                                       location.school.tt_ind])
            
    #When doing the post-improvement procedure, adding a student
    #also requires adding the school.
    def add_student(self, student):
        if student.type != self.locations[0].type:  #Different age group
            return False
        self.temp_backup()
        #First, add the school as late as possible.
        if student.school not in self.locations:
            if not self.insert_school(student.school):
                self.temp_restore()
                return False
        #Then add the student before the school.
        if not self.insert_mincost(student,
                                   post=self.locations.index(student.school) + 1):
            self.temp_restore()
            return False
        self.max_time = max(self.max_time,
                            constants.SLACK*constants.TRAVEL_TIMES[student.tt_ind,
                                                                   student.school.tt_ind])
        #self.two_opt()
        if self.feasibility_check():
            return True
        #If the feasibility check failed, need to revert the change.
        self.temp_restore()
        return False
        
    def get_route_length(self):
        return self.length
    
    #Performs an insertion of a Location at an index
    #in the travel time matrix such that the cost is
    #minmized.
    #pre and post allow enforcement of precedence relations
    #pre=-1 is a default value, post=-1 is just a placeholder
    def insert_mincost(self, location, pre = -1, post = -1):
        if post == -1:  #Replace the placeholder
            post = len(self.locations) + 1
        best_cost = 100000
        best_cost_ind = -1
        for i in range(pre+1, post):
            cost = 0
            if i > 0:
                cost += constants.TRAVEL_TIMES[self.locations[i-1].tt_ind,
                                               location.tt_ind]
            if i < len(self.locations):
                cost += constants.TRAVEL_TIMES[location.tt_ind,
                                               self.locations[i].tt_ind]
            if i > 0 and i < len(self.locations):
                cost -= constants.TRAVEL_TIMES[self.locations[i-1].tt_ind,
                                               self.locations[i].tt_ind]
            if cost < best_cost:
                best_cost = cost
                best_cost_ind = i
        if best_cost_ind > -1:
            self.length += best_cost
            if isinstance(location, Student):
                self.occupants += 1
            self.locations = (self.locations[:best_cost_ind] + [location] +
                              self.locations[best_cost_ind:])
            return True
        #If insertion fails, e.g. because [pre+1,post) is empty
        return False
    
    #When inserting a school, we choose to insert it as late as
    #possible while maintaining validity w.r.t bell times.
    def insert_school(self, school):
        if school in self.locations:
            return
        #Need to test all possible insertion locations.
        #Start by testing adding to the end, which is a special case
        self.locations = self.locations + [school]
        self.length += constants.TRAVEL_TIMES[self.locations[-2].tt_ind,
                                              self.locations[-1].tt_ind]
        #Perform the feasibility check, which among other things
        #tests bell time validity
        if self.feasibility_check():
            return True
        else:
            self.temp_restore()
        #Now test all possible locations in the middle
        for i in range(len(self.locations) - 1, 0, -1):
            self.length += constants.TRAVEL_TIMES[self.locations[i-1].tt_ind,
                                                  school.tt_ind]
            self.length += constants.TRAVEL_TIMES[school.tt_ind,
                                                  self.locations[i].tt_ind]
            self.length -= constants.TRAVEL_TIMES[self.locations[i-1].tt_ind,
                                                  self.locations[i].tt_ind]
            if self.length > self.max_time:
                self.temp_restore()
                continue
            self.locations = self.locations[:i] + [school] + self.locations[i:]
            if self.feasibility_check():
                return True
            else:
                self.temp_restore()
        return False
        
    
    #Performs the two-opt improvement procedure to try to
    #improve route quality
    #Note: Not every 2-opt improvement will be a global improvement
    #due to asymmetry of the travel time matrix, so it's necessary
    #to either check or just accept that some improvements will
    #be failures. For now, we'll take the easy way out.
    def two_opt(self):
        modified = False
        for i in range(len(self.locations) - 3):
            if isinstance(self.locations[i], School):
                break
            for j in range(i+2, len(self.locations) - 1):
                if isinstance(self.locations[j], School):
                    break
                existing_length = constants.TRAVEL_TIMES[self.locations[i].tt_ind,
                                                         self.locations[i+1].tt_ind]
                existing_length += constants.TRAVEL_TIMES[self.locations[j].tt_ind,
                                                          self.locations[j+1].tt_ind]
                modlength = constants.TRAVEL_TIMES[self.locations[i].tt_ind,
                                                   self.locations[j].tt_ind]
                modlength += constants.TRAVEL_TIMES[self.locations[i+1].tt_ind,
                                                    self.locations[j+1].tt_ind]
                if modlength < existing_length:
                    modified = True
                    self.locations[i+1:j+1] = self.locations[i+1:j+1][::-1]
                    self.recompute_length()
        if modified:
            return True
        return False
        
    #If there is ever uncertainty about the length field, recompute length
    def recompute_length(self):
        self.length = 0
        for i in range(len(self.locations) - 1):
            self.length += constants.TRAVEL_TIMES[self.locations[i].tt_ind,
                                                  self.locations[i+1].tt_ind]
        return self.length
    
    def recompute_occs(self):
        self.occupants = 0
        for loc in self.locations:
            if isinstance(loc, Student):
                self.occupants += 1
        return self.occupants
    
    def recompute_maxtime(self):
        for loc in self.locations:
            if isinstance(loc, Student):
                self.max_time = max(self.max_time, constants.SLACK*
                                    constants.TRAVEL_TIMES[loc.tt_ind,
                                                           loc.school.tt_ind])
    
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
        earliest_possible = 0
        latest_possible = 100000
        waiting_time = 0
        for i in range(1, len(self.locations)):
            dist = constants.TRAVEL_TIMES[self.locations[i - 1].tt_ind,
                                          self.locations[i].tt_ind]
            earliest_possible += dist
            latest_possible += dist
            if isinstance(self.locations[i], School):
                earliest_arrival = self.locations[i].start_time-constants.EARLIEST
                latest_arrival = self.locations[i].start_time-constants.LATEST
                #can't get to the school in time - give up
                if latest_arrival < earliest_possible:
                    return False
                #get to the school too early - add slack time
                if earliest_arrival > latest_possible:
                    waiting_time += earliest_arrival - latest_possible
                earliest_possible = max(earliest_possible, earliest_arrival)
                latest_possible = min(latest_possible, latest_arrival)
        if self.length + waiting_time > self.max_time:
            if verbose:
                print("Too long when considering bells")
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
    
    #Intended to help with greedy moves.
    #Remove the student at locations index ind and all subsequent
    #students with the same tt_ind and school.
    #Additionally see whether the student's school can be removed
    #ind must index a Student, not a School.
    #Add these locations to the other route.
    def remove_and_add(self, ind, other_route):
        tt_ind = self.locations[ind].tt_ind
        school = self.locations[ind].school
        postind = ind + 1
        while postind < len(self.locations):
            if (isinstance(self.locations[postind], School) or
                self.locations[postind].tt_ind != tt_ind or
                self.locations[postind].school != school):
                break
            postind += 1
        for i in range(tt_ind, postind):
            if not other_route.add_student(self.locations[i]):
                return False
        self.locations = self.locations[:tt_ind] + self.locations[postind:]
        self.recompute_length()
        self.recompute_maxtime()
        for loc in self.locations:
            if isinstance(loc, Student) and loc.school == school:
                return True
        self.locations.remove(school)
        self.recompute_length()
        self.recompute_maxtime()
        return True