class School:
    
    #tt_ind denotes the index of the school in the travel time matrix.
    #start_time is in seconds since midnight
    def __init__(self, tt_ind, start_time):
        self.tt_ind = tt_ind
        self.start_time = start_time

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