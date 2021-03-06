import constants
import copy

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]

class School:
    
    #tt_ind denotes the index of the school in the travel time matrix.
    #start_time and end_time are in seconds since midnight
    #unrouted_stops is the set of stops for that school
    #that are not unrouted
    #type is the school's type of student attendee ('E', 'M', 'H')
    #unrouted_stops is the dict from age group to set of stops for
    #the school which are not routed
    def __init__(self, school_identifier, tt_ind, start_time, end_time,
                 school_name = None, ridership_probability = 1.0):
        self.school_identifier = school_identifier
        self.tt_ind = tt_ind
        self.start_time = start_time
        self.earliest_dropoff = self.start_time - constants.EARLIEST_AM
        self.latest_dropoff = self.start_time - constants.LATEST_AM
        self.end_time = end_time
        self.earliest_pickup = self.start_time + constants.EARLIEST_PM
        self.latest_pickup = self.start_time + constants.LATEST_PM
        self.unrouted_stops = set()
        self.school_name = school_name
        self.ridership_probability = ridership_probability
        
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
    #For the purposes of the uncrossing code, adding a return_ratio
    #argument. If it's true, return the ratio of capacity used
    #to available capacity instead of just returning a boolean
    #storing whether the bus can handle the route.
    def can_handle(self, r, suppress_already_assigned_check = False,
                   return_ratio = False):
        #If already assigned to a route, can't do another
        if self.route != None and not suppress_already_assigned_check:
            return False
        #If lacks a required lift, doesn't work
        if not self.lift:
            for stop in r.stops:
                if stop.count_needs("W") > 0 or stop.count_needs("L") > 0:
                    return False
        #If it's only one stop, automatically allowed, as it's considered
        #infeasible to split stops among multiple routes
        if len(r.stops) == 1:
            return True
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
                #HCA, private nurse, supervisor: takes up a full bench.
                if stud.has_need('I'):
                    hca += 1
                if stud.has_need('A'):
                    sup_required = True
                    #Wheelchair: decreases the capacity
                if stud.has_need('W'):
                    num_wheelchair += 1
                    continue
                e += (stud.type == 'E')*stop.ridership_probability()
                m += (stud.type == 'M')*stop.ridership_probability()
                h += (stud.type == 'H')*stop.ridership_probability()
        #If we have fewer than the minimum number of wheelchair
        #students, usable space will be sitting empty.
        if (num_wheelchair < self.num_wheelchair_min):
            h += 2*(self.num_wheelchair_min - num_wheelchair)
        h += (hca+sup_required)*2
        h += (num_wheelchair)*3
        #If we have more than the maximum number of wheelchair
        #students, infeasible.
        if (num_wheelchair > self.num_wheelchair_max):
            return False
        #Not enough back seats for students with machines
        if machine > 2:
            return False
        #Failsafe if the number of wheelchair students
        #eliminates the possibility of any others
        if min(mod_caps) < 0 or (min(mod_caps) == 0 and e+m+h > 0):
            return False
        prop_occupied = (e/mod_caps[0] + m/mod_caps[1] + h/mod_caps[2])
        if return_ratio:
            return prop_occupied
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
    #file_index is which row of the students file the student is in
    #For now, ridership probability is not used, but it will be
    #needed if we try to implement overbooking.
    def __init__(self, tt_ind, school, age_type, fields, file_index, student_id_number, needs = None):
        self.tt_ind = tt_ind
        self.school = school
        self.type = age_type
        self.fields = fields
        self.file_index = file_index
        self.needs = dict()
        self.stop = None
        self.student_id_number = student_id_number
        
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
        
    def ridership_probability(self):
        return self.school.ridership_probability
        
    def add_student(self, s):
        if s.type == 'E':
            self.e += 1
        if s.type == 'M':
            self.m += 1
        if s.type == 'H':
            self.h += 1
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