import numpy as np
import random as random
max_time = 3600

#Similar to basicnearneighbor, but when constructing a route using nearest-
#neighbor, starts at the school and works backwards. Should be better than
#taking a random starting point.


#Warning: The travel times matrix is a global variable.
prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/data/"
travel_times = np.load(prefix + "travel_time_matrix.npy")

class School:
    
    #tt_ind denotes the index of the school in the travel time matrix
    def __init__(self, tt_ind):
        self.tt_ind = tt_ind

class Student:
    
    #tt_ind denotes the index of the student's stop in the
    #travel time matrix
    #school_id is the index of the cost center (attendance location)
    #in the travel time matrix
    #for now, ridership probability is not used
    def __init__(self, tt_ind, school_ind, rider_prob = 1.0):
        self.tt_ind = tt_ind
        self.school_ind = school_ind
        self.bus_assigned = False
        self.rider_prob = rider_prob
        
class Route:
    
    #For now, encapsulated as a list of student/stop index pairs in order
    def __init__(self, tt_ind):
        self.students = []
        self.length = 0
        self.occupants = 0
        self.tt_ind = tt_ind
        
    #insert a student pickup at a certain position in the route.
    #default position is the end
    def add_student(self, student, pos = -1):
        self.students = self.students[:pos] + [student] + self.students[pos:]
        if (pos == -1 and len(self.students) > 1) or pos > 0:
            self.length += travel_times[self.students[pos - 1].tt_ind,
                                        self.students[pos].tt_ind]
        if pos > -1 and pos < len(self.students) - 1:
            self.length += travel_times[self.students[pos].tt_ind,
                                        self.students[pos + 1].tt_ind]
            
        self.occupants += 1
        
    def get_schoolless_route_length(self):
        return self.length
        
    def get_route_length(self):
        return self.length + travel_times[self.students[-1].tt_ind,
                                          self.tt_ind]
        
#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

#phonebooks: list of filenames for phonebooks
#phonebooks are assumed to be in the format that was provided to
#me in early November 2018
#all_geocodes: filename for list of all geocodes. gives map from geocode to ind
#geocoded_stops: file name for map from stop to geocode
#geocoded_schools: file name for map from school to geocode
#returns a list of all students, a dict from schools to sets of
#students, and a dict from schools to indices in the travel time matrix.
def setup_students(phonebooks, all_geocodes, geocoded_stops, geocoded_schools):
    
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    schools = open(geocoded_schools, 'r')
    schools_codes_map = dict()
    schools_students_map = dict()  #maps schools to sets of students
    schools.readline()  #get rid of header
    for cost_center in schools.readlines():
         fields = cost_center.split(";")
         if len(fields) < 8:
             continue
         schools_codes_map[fields[1]] = (fields[6].strip() + ";"
                                         + fields[7].strip())
         schools_students_map[fields[1]] = set()
    schools.close()
    
    geocodes = open(all_geocodes, 'r')
    codes_inds_map = dict()
    ind = 0
    for code in geocodes.readlines():
        codes_inds_map[code.strip()] = ind
        ind += 1
    geocodes.close()
    
    schools_inds_map = dict()
    for school in schools_codes_map:
        schools_inds_map[school] = codes_inds_map[schools_codes_map[school]]
    
    students = []
    bus_col = 12
    for pb_part_filename in phonebooks:
        pb_part = open(pb_part_filename, 'r')
        pb_part.readline()  #header
        for student_record in pb_part.readlines():
            fields = student_record.split(";")
            if len(fields) <= bus_col + 6:
                continue
            if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
                continue
            if fields[bus_col - 1].strip() == "9500":  #walker
                continue
            if fields[bus_col + 2].strip() not in ["1", "01"]:  #not first trip
                continue
            if fields[1].strip() == "":  #no school given
                continue
            #For now, I won't consider special ed.
            #Will be necessary to add later.
            #if fields[5].strip() not in ["M", "X"]:
            #    continue
            stop = californiafy(fields[bus_col + 6])
            school = fields[1].strip()
            stop_ind = codes_inds_map[stops_codes_map[stop]]
            school_ind = codes_inds_map[schools_codes_map[school]]
            this_student = Student(stop_ind, school_ind)
            students.append(this_student)
            schools_students_map[school].add(this_student)
        pb_part.close()
        
    return students, schools_students_map, schools_inds_map

#bus_capacities is an input csv file where the first
#column is bus ID and the second is capacity.
def setup_buses(bus_capacities):
    cap_counts_dict = dict()  #map from capacities to # of buses of that capacity
    caps = open(bus_capacities, 'r')
    for bus in caps.readlines():
        fields = bus.split(";")
        cap = int(fields[1])
        if cap not in cap_counts_dict:
            cap_counts_dict[cap] = 0
        cap_counts_dict[cap] += 1
    caps.close()
    #now turn into a list sorted by capacity
    cap_counts_list = list(cap_counts_dict.items())
    cap_counts_list = sorted(cap_counts_list, key = lambda x:x[0])
    for i in range(len(cap_counts_list)):
        cap_counts_list[i] = list(cap_counts_list[i])
    return cap_counts_list

#Determines the closest pair of locations in from_iter and to_iter
#from_iter and to_iter should both be iterables of Students and/or Schools
def closest_pair(from_iter, to_iter):
    opt_dist = 100000
    opt_from_loc = None
    opt_to_loc = None
    for from_loc in from_iter:
        for to_loc in to_iter:
            if travel_times[from_loc.tt_ind,
                            to_loc.tt_ind] < opt_dist:
                opt_dist = travel_times[from_loc.tt_ind,
                                       to_loc.tt_ind]
                opt_from_loc = from_loc
                opt_to_loc = to_loc
    return opt_from_loc, opt_to_loc

#WARNING: Empties set of route students
#Students is most efficient as a set
#Students must be nonempty
def single_route(route_students, school_ind):
    #simply creates nearest neighbor route for now
    route = Route(school_ind)
    #last student to pick up is the one nearest the school
    init_student = closest_pair(route_students, [School(school_ind)])[0]
    route.add_student(init_student)
    route_students.remove(init_student)
    while len(route_students) > 0:
        to_add = closest_pair(route_students, [route.students[0]])[0]
        #add student to beginning of route
        route.add_student(to_add, pos = 0)
        route_students.remove(to_add)
    return route
                    
        
#student_set is the set of students attending the school
#cap_counts is a list of [bus capacity, count] pairs sorted by capacity
#max_time is in seconds
#school_ind is the index in the travel time matrix
def route_school(student_set, cap_counts, max_time, school_ind):
    school_students= list(student_set)
    route_set = set()
    while len(school_students) > 0:
        init_student = closest_pair(school_students, [School(school_ind)])[0]
        current_students = set()
        current_students.add(init_student)
        school_students.remove(init_student)
        current_route = single_route(list(current_students), school_ind)
        while True:
            #no bus of large enough capacity exists to take more students
            if len(current_students) + 1 > cap_counts[-1][0]:
                break
            #all students are routed
            if len(school_students) == 0:
                break
            #find the student nearest any student on the route
            student_to_add = closest_pair(current_students, school_students)[1]
            current_students.add(student_to_add)
            new_route = single_route(list(current_students), school_ind)
            #if the computed route is too long to add this student,
            #route is finished
            if new_route.get_route_length() > max_time:
                current_students.remove(student_to_add)
                break
            current_route = new_route
            school_students.remove(student_to_add)
        route_set.add(current_route)
        for bus_ind in range(len(cap_counts)):
            bus = cap_counts[bus_ind]
            #found the smallest suitable bus
            if current_route.occupants <= bus[0]:
                #mark the bus as taken
                bus[1] -= 1
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    cap_counts.remove(bus)
                break
            
prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/data/csvs/"
output = setup_students([prefix+'phonebook_parta.csv',
                         prefix+'phonebook_partb.csv'],
                         prefix+'all_geocodes.csv',
                         prefix+'stop_geocodes_fixed.csv',
                         prefix+'school_geocodes_fixed.csv')
students = output[0]
schools_students_map = output[1]
schools_inds_map = output[2]
cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
print(len(students))
print(len(schools_students_map))
print(cap_counts)
tot_cap = 0
for bus in cap_counts:
    tot_cap += bus[0]*bus[1]
print("Total capacity: " + str(tot_cap))

tot = 0
for school in schools_students_map:
    student_set = schools_students_map[school]
    result = route_school(student_set, cap_counts,
                          max_time, schools_inds_map[school])

    if len(student_set) > 0:
        print("Routed school of size " + str(len(student_set)))
        cur_tot_cap = 0
        for bus in cap_counts:
            cur_tot_cap += bus[0]*bus[1]
        print("Remaining capacity: " + str(cur_tot_cap))
        tot += len(student_set)
        print(tot)