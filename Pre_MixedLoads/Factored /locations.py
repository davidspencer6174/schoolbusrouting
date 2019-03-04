
class School:
    #tt_ind denotes the index of the school in the travel time matrix
    def __init__(self, tt_ind, cost_center, school_name):
        self.tt_ind = tt_ind
        self.cost_center = cost_center
        self.school_name = school_name

class Student:
    def __init__(self, tt_ind, school_ind):
        self.tt_ind = tt_ind
        self.school_ind = school_ind

class Route:
    #For now, encapsulated as a list of student/stop index pairs in order
    def __init__(self, path, path_info, school_path):
        self.students = []
        self.path = path
        self.path_info = path_info
        self.occupants = 0
        self.school_path = school_path
        self.schools_to_visit = set() 
        self.bus_size = None
    
    def get_route_length(self):
        return sum([i for i, j in self.path_info])

    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student):
        self.students.append(student)
        self.occupants += 1
    
    def updateBus(self, bus_cap):
        self.bus_size = bus_cap
    
    def updateSchoolsToVisit(self, student):
        self.schools_to_visit.add(student.school_ind)