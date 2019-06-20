import constants
import copy

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

class School:
    
    #tt_ind denotes the index of the school in the travel time matrix.
    #start_time is in seconds since midnight
    #unrouted_stops is the set of stops for that school
    #that are not unrouted
    #type is the school's type of student attendee ('E', 'M', 'H')
    #unrouted_stops is the dict from age group to set of stops for
    #the school which are not routed
    def __init__(self, tt_ind, start_time, school_name = None):
        self.tt_ind = tt_ind
        self.start_time = start_time
        self.unrouted_stops = set()
        self.school_name = school_name
        
class Bus:
    
    #capacity denotes the unmodified capacity of a bus.
    #num_wheelchair denotes the number of wheelchair spots
    #lift denotes whether the bus has a lift
    def __init__(self, capacity, num_wheelchair_min, num_wheelchair_max, lift):
        self.capacity = capacity
        self.num_wheelchair_min = num_wheelchair_min
        self.num_wheelchair_max = num_wheelchair_max
        self.lift = lift
        self.route = None
        
    def __str__(self):
        if not self.lift:
            return "Bus of capacity " + str(self.capacity)
        return ("Lift bus of capacity " + str(self.capacity) +
                " that can take " + str(self.num_wheelchair_min) +
                " to " + str(self.num_wheelchair_max) + " wheelchairs.")
        
    #For the sake of verifying correctness later, allow suppression
    #of the check for buses already being assigned.
    def can_handle(self, r, suppress_already_assigned_check = False):
        #If already assigned to a route, can't do another
        if self.route != None and not suppress_already_assigned_check:
            return False
        #If lacks a required lift, doesn't work
        if not self.lift:
            for stop in r.stops:
                if stop.count_needs("W") > 0 or stop.count_needs("L") > 0:
                    return False
        mod_caps = copy.copy(constants.CAPACITY_MODIFIED_MAP[self.capacity])
        e, m, h = 0, 0, 0
        hca = 0
        sup_required = False
        machine = 0
        num_wheelchair = 0
        for stop in r.stops:
            for stud in stop.students:
                #Machine user: needs to sit in the back
                if stud.has_need('M'):
                    machine += 1
                #Wheelchair: decreases the capacity
                if stud.has_need('W'):
                    mod_caps[0] -= 3
                    mod_caps[1] -= 2
                    mod_caps[2] -= 2
                    num_wheelchair += 1
                e += (stud.type == 'E')
                m += (stud.type == 'M')
                h += (stud.type == 'H')
                #HCA, private nurse, supervisor: takes up a full bench.
                if stud.has_need('I'):
                    hca += 1
                if stud.has_need('A'):
                    sup_required = True
        if (num_wheelchair < self.num_wheelchair_min or
            num_wheelchair > self.num_wheelchair_max):
            return False
        if machine > 2:
            return False
        h += 2*(hca + sup_required)
        #Failsafe if the number of wheelchair students
        #eliminates the possibility of any others
        if min(mod_caps) < 0 or (min(mod_caps) == 0 and e+m+h > 0):
            return False
        prop_occupied = (e/mod_caps[0] + m/mod_caps[1] + h/mod_caps[2] +
                        (hca+sup_required)*2/mod_caps[2])
        return (prop_occupied <= 1.0)
    
    #Assigns the bus to a route
    def assign(self, route):
        assert self.route == None, "Cannot assign a bus to multiple routes"
        possible = self.can_handle(route)
        if possible:
            self.route = route
            route.bus = self
        return possible

class Student:
    
    #tt_ind denotes the index of the student's stop in the
    #travel time matrix.
    #school is the student's school of attendance.
    #type is E (elementary), M (middle), H (high), O (other)
    #fields is the full list of entries to make it easier to
    #examine the saved routes.
    #For now, ridership probability is not used, but it will be
    #needed if we try to implement overbooking.
    def __init__(self, tt_ind, school, age_type, fields, needs = None):
        self.tt_ind = tt_ind
        self.school = school
        self.type = age_type
        self.fields = fields
        self.needs = dict()
        self.stop = None
        
    #Readable string representation
    def __str__(self):
        out = self.type
        if len(self.needs) == 0:
            return out + " M, X, or P student."
        out += " student with needs "
        for need in self.needs:
            out += need
            if self.needs[need] != True:
                out += str(self.needs[need])
            out += ", "
        return out[:-2]
        
    #Key-value pair where the key encapsulates the type of need.
    #Usually, the value is empty.
    #Needs:
    #'W' means the student needs a wheelchair, and thus 5 extra minutes.
    #'L' means the student is nonambulatory and needs a lift bus
    #but has no wheelchair, and thus 2 extra minutes.
    #'A' means adult supervision is required, but not one-on-one.
    #'I' means one-on-one supervision is required.
    #(a private nurse and HCA are treated the same way here).
    #'M' means a machine is required, and therefore the student needs
    #to be in a back seat (so only 2 such students can be on a bus)
    #Two such machines are suction machines and oxygen machines.
    #'T' means a time limit other than the default is required.
    #In this case, the value will be the number of seconds allowed.
    #'F' means the student needs to be the final student on the route.
    def add_need(self, need, value = True):
        self.needs[need] = value
        
    def has_need(self, need):
        return need in self.needs

    def need_value(self, need):
        return self.needs[need]
        
    
        
class Stop:
    
    #A stop is just a set of students at a stop who
    #attend a particular school.
    #students contains all students, special_ed_students keeps track
    #of the special ed students
    def __init__(self, school):
        self.students = set()
        self.special_ed_students = set()
        self.school = school
        self.e = 0
        self.m = 0
        self.h = 0
        self.tt_ind = None
        self.occs = 0
        #We will assign each stop a value; routes will strive
        #to pick up the stops with the most value.
        self.value = -1000
        #Keep track of the nearest Stop from its school, or the
        #School itself if it happens to be closest.
        #The farther it is, the more valued this stop is.
        #If dependent is a Stop, when it gets routed, we need
        #to update, so we store it for the sake of memoization.
        self.dependent = None
        
    def add_student(self, s):
        if s.type == 'E':
            self.e += 1
        if s.type == 'M':
            self.m += 1
        if s.type == 'H':
            self.h += 1
        if self.tt_ind != None and self.tt_ind != s.tt_ind:
            print("Conflicting tt_inds at a stop")
        self.students.add(s)
        if len(s.needs) > 0:
            self.special_ed_students.add(s)
        self.tt_ind = s.tt_ind
        self.occs += 1
        s.stop = self
        return True
    
    #Determine how many students have a particular need
    def count_needs(self, need):
        tot = 0
        for stud in self.special_ed_students:
            if stud.has_need(need):
                tot += 1
        return tot
    
    #Figure out how much extra time is needed for wheelchair/lift
    def extra_time(self):
        if self.count_needs("W") > 0:
            return constants.WHEELCHAIR_STOP_TIME
        if self.count_needs("L") > 0:
            return constants.LIFT_STOP_TIME
        return 0
    
    def update_value(self, removed_stop):
        #If our dependent was not removed, no need to update
        if self.dependent != None and removed_stop != self.dependent:
            return
        self.value = -1000
        for stop in self.school.unrouted_stops:
            if self == stop:
                continue
            value = (trav_time(self, self.school)*constants.SCH_DIST_WEIGHT +
                     trav_time(self, stop)*constants.STOP_DIST_WEIGHT)
            if value > self.value:
                self.value = value
                self.dependent = stop
        value = trav_time(self, self.school)*(constants.SCH_DIST_WEIGHT +
                                              constants.STOP_DIST_WEIGHT)
        if value > self.value:
            self.value = value
            self.dependent = self.school