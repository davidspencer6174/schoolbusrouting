class School:
    
    #tt_ind denotes the index of the school in the travel time matrix.
    #start_time is in seconds since midnight
    #unrouted_stops is the set of stops for that school
    #that are not unrouted
    #type is the school's type of student attendee ('E', 'M', 'H')
    #unrouted_stops is the dict from age group to set of stops for
    #the school which are not routed
    def __init__(self, tt_ind, start_time):
        self.tt_ind = tt_ind
        self.start_time = start_time
        self.unrouted_stops = dict()
        self.unrouted_stops['E'] = set()
        self.unrouted_stops['M'] = set()
        self.unrouted_stops['H'] = set()

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
    def __init__(self, school, stud_type):
        self.students = set()
        self.school = school
        self.type = stud_type
        self.routed = False
        self.tt_ind = None
        self.occs = 0
        
    def add_student(self, s):
        if s.type != self.type:
            print(s.type)
            print(self.type)
            print("Student is not the right age to be added to this stop")
            return False
        self.students.add(s)
        self.tt_ind = s.tt_ind
        self.occs += 1
        return True