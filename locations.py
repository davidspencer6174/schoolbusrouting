import constants

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

class Student:
    
    #tt_ind denotes the index of the student's stop in the
    #travel time matrix.
    #school is the student's school of attendance.
    #type is E (elementary), M (middle), H (high), O (other)
    #fields is the full list of entries to make it easier to
    #examine the saved routes.
    #For now, ridership probability is not used, but it will be
    #needed if we try to implement overbooking.
    def __init__(self, tt_ind, school, age_type, fields, rider_prob = 1.0):
        self.tt_ind = tt_ind
        self.school = school
        self.type = age_type
        self.fields = fields
        self.rider_prob = rider_prob
        
class Stop:
    
    #A stop is just a set of students at a stop who
    #attend a particular school.
    def __init__(self, school):
        self.students = set()
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
        self.tt_ind = s.tt_ind
        self.occs += 1
        return True
    
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