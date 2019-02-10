import numpy as np
import random as random
import copy as copy
import pickle


#Modifying nnradd2opt to allow mixed loads.


#Warning: The travel times matrix is a global variable.
prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//"
travel_times = np.load(prefix + "travel_time_matrix.npy")
#Additionally, the max time variable is global.
max_time = 3600
#Assumed multiplier due to traffic
traffic_mult = 1.5
travel_times *= traffic_mult

#Create a map from grade level to student type (elemntary, etc.)
grades_types_map = dict()
for i in range(1, 6):
    grades_types_map[i] = 'E'
for i in range(6, 9):
    grades_types_map[i] = 'M'
for i in range(9, 13):
    grades_types_map[i] = 'H'

verbose = True

#Seconds before belltime to determine valid arrival
#Valid arrival times are [belltime-earliest, belltime-latest]
earliest = 1800
latest = 600
#earliest = 10000
#latest = 0

#I'll be thinking of both Schools and Students as Locations, which
#have the tt_ind field.
#Note: Locations should be considered immutable.

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
    def __init__(self, tt_ind, school, stud_type, fields, rider_prob = 1.0):
        self.tt_ind = tt_ind
        self.school = school
        self.type = stud_type
        self.fields = fields
        self.rider_prob = rider_prob
        
class Route:
    
    #For now, encapsulated as a list of Locations in order.
    def __init__(self):
        self.locations = []
        self.length = 0
        self.occupants = 0
        self.backup_locs = []
        self.backup_occs = 0
        #If no bus is assigned, the default capacity is infinite.
        #This is denoted by a -1.
        #Otherwise, this variable should be modified to reflect
        #the actual capacity.
        self.bus_capacity = -1
        
    #This is a backup used during the mixed-load post improvement
    #procedure when it is determined that a bus cannot be deleted,
    #and so all routes must be reverted and the moved students
    #returned to the bus.    
    def backup(self):
        self.backup_locs = copy.copy(self.locations)
        self.backup_occs = self.occupants
        self.backup_length = self.length
        
    def restore(self):
        self.locations = self.backup_locs
        self.occupants = self.backup_occs
        self.length = self.backup_length
        
    #This is a backup used when attempting to add a single student
    #to a route. A backup will be made, the route will be modified
    #to add the student, the feasibility check will be performed,
    #and if the modified route is infeasible, the change will be reverted.
    def temp_backup(self):
        self.temp_backup_locs = copy.copy(self.locations)
        self.temp_backup_occs = self.occupants
        self.temp_backup_length = self.length
        
    def temp_restore(self):
        self.locations = self.temp_backup_locs
        self.occupants = self.temp_backup_occs
        self.length = self.temp_backup_length
        
    #Inserts a Location visit at position pos in the route.
    #The default position is the end.
    #Does not do any checks.
    def add_location(self, location, pos = -1):
        #Add the location
        self.locations = self.locations[:pos] + [location] + self.locations[pos:]
        #Maintain the travel time field
        if (pos == -1 and len(self.locations) > 1) or pos > 0:
            self.length += travel_times[self.locations[pos - 1].tt_ind,
                                        self.locations[pos].tt_ind]
        if pos > -1 and pos < len(self.locations) - 1:
            self.length += travel_times[self.locations[pos].tt_ind,
                                        self.locations[pos + 1].tt_ind]
        #Maintain the occupants field
        if isinstance(location, Student):
            self.occupants += 1
            
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
                                   post=self.locations.index(student.school)):
            self.temp_restore()
            return False
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
                cost += travel_times[self.locations[i-1].tt_ind,
                                     location.tt_ind]
            if i < len(self.locations):
                cost += travel_times[location.tt_ind,
                                     self.locations[i].tt_ind]
            if i > 0 and i < len(self.locations):
                cost -= travel_times[self.locations[i-1].tt_ind,
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
        self.locations = self.locations + [school]
        self.length += travel_times[self.locations[-2].tt_ind,
                                    self.locations[-1].tt_ind]
        if self.feasibility_check():
            return True
        else:
            self.temp_restore()
        for i in range(len(self.locations) - 1, 0, -1):
            self.length += travel_times[self.locations[i-1].tt_ind,
                                        school.tt_ind]
            self.length += travel_times[school.tt_ind,
                                        self.locations[i].tt_ind]
            self.length -= travel_times[self.locations[i-1].tt_ind,
                                        self.locations[i].tt_ind]
            if self.length > max_time:
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
            for j in range(i+2, len(self.locations) - 1):
                existing_length = travel_times[self.locations[i].tt_ind,
                                               self.locations[i+1].tt_ind]
                existing_length += travel_times[self.locations[j].tt_ind,
                                                self.locations[j+1].tt_ind]
                modlength = travel_times[self.locations[i].tt_ind,
                                          self.locations[j].tt_ind]
                modlength += travel_times[self.locations[i+1].tt_ind,
                                           self.locations[j+1].tt_ind]
                if modlength < existing_length:
                    modified = True
                    self.locations[i+1:j+1] = self.locations[i+1:j+1][::-1]
                    self.recompute_length()
        if modified:
            return True
        return False
        
    #Modifies the length field
    def recompute_length(self):
        self.length = 0
        for i in range(len(self.locations) - 1):
            self.length += travel_times[self.locations[i].tt_ind,
                                        self.locations[i+1].tt_ind]
        return self.length
    
    #Determines whether the route is feasible with
    #respect to constraints.
    #Simple for now
    def feasibility_check(self):
        if self.length > max_time:
            return False
        if self.bus_capacity > -1 and self.occupants > self.bus_capacity:
            return False
        earliest_possible = 0
        latest_possible = 100000
        for i in range(len(self.locations) - 1, 0, -1):
            dist = travel_times[self.locations[i-1].tt_ind,
                                self.locations[i].tt_ind]
            earliest_possible -= dist
            latest_possible -= dist
            if isinstance(self.locations[i], School):
                earliest_possible = max(earliest_possible,
                                        self.locations[i].start_time-earliest)
                latest_possible = min(latest_possible,
                                      self.locations[i].start_time-latest)
            if latest_possible < earliest_possible:
                return False
        return True
        
        
#Perform the mixed-load improvement procedure on a list of routes.
#This function does require it to be a list rather than a
#general Iterable, since it deletes while iterating.
def mixed_loads(route_list):
    #Iterate over all routes and check whether they
    #can be removed.
    buses_saved = []
    print("Old number of routes: " + str(len(route_list)))
    i = 0
    while i < len(route_list):
        if (len(route_list) - i) % 50 == 0:
            if verbose:
                print((len(route_list) - i))
        route_to_delete = route_list[i]
        #Make backups to revert if the deletion fails
        for route in route_list:
            route.backup()
        locations = route_to_delete.locations
        #succeeded will be set to false if we find
        #a student who cannot be moved.
        succeeded = True
        for location in locations:
            #If this is a student, find a route to add to
            if isinstance(location, Student):
                moved = False
                for route_to_add_to in route_list:
                    if (route_to_add_to != route_to_delete and
                        route_to_add_to.add_student(location)):
                        moved = True
                        break
                if not moved:
                    succeeded = False
        if not succeeded:
            for route in route_list:
                route.restore()
        else:
            if verbose:
                print("Successfully deleted a route")
            buses_saved.append(route_to_delete.bus_capacity)
            del route_list[i]
            i -= 1
        i += 1
        #if i > 200:  #for the purposes of obtaining quicker profiling results
        #    break
    print("New number of routes: " + str(len(route_list)))
    return buses_saved
        
                    
        

#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

#Bit of a hack to compute seconds since midnight
def timesecs(time_string):
    pieces = time_string.split(':')
    minutes = int(pieces[1][:2])  #minutes
    minutes += 60*int(pieces[0])  #hours
    if 'p' in pieces[1].lower():  #PM
        minutes += 12*60
    return minutes*60



#phonebooks: list of filenames for phonebooks
#phonebooks are assumed to be in the format that was provided to
#me in early November 2018
#all_geocodes: filename for list of all geocodes. gives map from geocode to ind
#geocoded_stops: file name for map from stop to geocode
#geocoded_schools: file name for map from school to geocode
#returns a list of all students, a dict from schools to sets of
#students, and a dict from schools to indices in the travel time matrix.
#bell_sched: file name for which column 3 is cost center and
#column 4 is start time
def setup_students(phonebooks, all_geocodes, geocoded_stops,
                   geocoded_schools, bell_sched):
    
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    belltimes = open(bell_sched, 'r')
    centers_times_map = dict()  #maps cost centers to times in seconds
    belltimes.readline()  #get rid of header
    for bell_record in belltimes.readlines():
        fields = bell_record.split(";")
        centers_times_map[fields[3]] = timesecs(fields[4])
    
    schools = open(geocoded_schools, 'r')
    schools_codes_map = dict()  #maps schools to geocodes
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
    #Maintain a dictionary of school indices to schools so that
    #school objects can be tested for equality.
    ind_school_dict = dict()
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
            if fields[5].strip() not in ["M", "X"]:
                continue
            stop = californiafy(fields[bus_col + 6])
            school = fields[1].strip()  #Cost center id
            stop_ind = codes_inds_map[stops_codes_map[stop]]
            school_ind = codes_inds_map[schools_codes_map[school]]
            grade = fields[3].strip()  #Grade level
            student_type = 'Other'
            try:
                grade = int(grade)
            except:
                grade = -1
            if int(grade) in grades_types_map:
                student_type = grades_types_map[int(grade)]
            if school_ind not in ind_school_dict:
                belltime = 8*60*60  #default to 8AM start
                #None of the 19xxxxx schools have start times.
                if school in centers_times_map:
                    belltime = centers_times_map[school]
                else:
                    if verbose:
                        print("No time given for " + school)                    
                ind_school_dict[school_ind] = School(school_ind, belltime)
            this_student = Student(stop_ind, ind_school_dict[school_ind],
                                   student_type, fields)
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

#Determines a closest pair of locations in from_iter and to_iter
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
def single_route(route_students, school):
    #simply creates nearest neighbor route for now
    route = Route()
    #initialize route with just school
    route.add_location(school)
    while len(route_students) > 0:
        to_add = closest_pair(route_students, [route.locations[0]])[0]
        #add student to beginning of route
        route.add_location(to_add, pos = 0)
        route_students.remove(to_add)
    route.two_opt()
    return route

#Verifies the routes without relying on the fields of the
#routes, i.e. computes travel time and occupants from
#scratch.
def full_verification(routes, max_time, print_result = False):
    valid = True
    students = set()
    for route in routes:
        if not route.feasibility_check():
            print("Ordinary check failed")
            return False
        time = 0
        locations = route.locations
        for i in range(len(locations) - 1):
            time += travel_times[locations[i].tt_ind, locations[i+1].tt_ind]
        if time > max_time:
            valid = False
            print("Max time violated")
        for loc_ind in range(len(locations)):
            loc = locations[loc_ind]
            if isinstance(loc, Student):
                students.add(loc)
                if loc.school not in locations[loc_ind+1:]:
                    print("Did not visit student's school")
                    valid = False
    if print_result:
        print("Completed route verification process.")
    if valid:
        if print_result:
            print(str(len(students)) + " students successfully routed.")
        return True    
    if print_result:
        print("At least one invalid route was found.")
    return False
                    
        
#student_set is the set of students attending the school
#cap_counts is a list of [bus capacity, count] pairs sorted by capacity
#max_time is in seconds
#school_ind is the index in the travel time matrix
def route_school(student_set, cap_counts, contr_counts, max_time, school):
    
    school_students = list(student_set)
    route_set = set()
    while len(school_students) > 0:
        init_student = closest_pair(school_students, [school])[0]
        current_students = set()
        current_students.add(init_student)
        school_students.remove(init_student)
        current_route = single_route(list(current_students), school)
        while True:
            #used all district buses and no contract bus is large enough
            if (len(cap_counts) == 0 and
                len(current_students) + 1 > contr_counts[-1][0]):
                break
            #no district bus of large enough capacity exists to
            #take more students
            if (len(cap_counts) > 0 and
                len(current_students) + 1 > cap_counts[-1][0]):
                break
            #all students are routed
            if len(school_students) == 0:
                break
            #find the student nearest any student on the route
            student_to_add = closest_pair(current_students, school_students)[1]
            current_students.add(student_to_add)
            new_route = single_route(list(current_students), school)
            #if the computed route is too long to add this student,
            #route is finished
            if new_route.get_route_length() > max_time:
                current_students.remove(student_to_add)
                break
            current_route = new_route
            school_students.remove(student_to_add)
        route_set.add(current_route)
        #Look for the district bus that can accommodate the route
        for bus_ind in range(len(cap_counts)):
            bus = cap_counts[bus_ind]
            #found the smallest suitable bus
            if current_route.occupants <= bus[0]:
                #mark the bus as taken
                bus[1] -= 1
                #Update the route to know the bus capacity
                current_route.bus_capacity = bus[0]
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    cap_counts.remove(bus)
                break
        #If all district buses have been used, use a contract bus.
        if len(cap_counts) == 0:
            for bus_ind in range(len(contr_counts)):
                bus = contr_counts[bus_ind]
                if current_route.occupants <= bus[0]:
                    bus[1] += 1
                    current_route.bus_capacity = bus[0]
                    break
    return route_set
            
    
    
def main():
    prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//csvs//"
    output = setup_students([prefix+'phonebook_parta.csv',
                             prefix+'phonebook_partb.csv'],
                             prefix+'all_geocodes.csv',
                             prefix+'stop_geocodes_fixed.csv',
                             prefix+'school_geocodes_fixed.csv',
                             prefix+'bell_times.csv')
    students = output[0]
    schools_students_map = output[1]
    schools_inds_map = output[2]
    cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
    #So far, we are using 0 of each contract size.
    #This will get incremented when the schools get routed.
    contr_counts = [[8, 0], [12, 0], [25, 0], [39, 0], [65, 0]]
    if verbose:
        print(len(students))
        print(len(schools_students_map))
        print(cap_counts)
    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]
            
    if verbose:
        print("Total capacity: " + str(tot_cap))

    tot = 0
    all_routes = list()
    
    schoolsstudents = schools_students_map.items()
    schoolsstudents = sorted(schoolsstudents, key = lambda x:-len(x[1]))
    for schoolsetpair in schoolsstudents:
        student_set = schoolsetpair[1]
        school_to_route = None
        for student in student_set:  #get the school from a student
            school_to_route = student.school
            break
        for route in route_school(student_set, cap_counts, contr_counts,
                                  max_time, school_to_route):
            all_routes.append(route)
            if len(student_set) > 0:
                if verbose:
                    print("Routed school of size " + str(len(student_set)))
                cur_tot_cap = 0
            for bus in cap_counts:
                cur_tot_cap += bus[0]*bus[1]
            if verbose:
                print("Remaining capacity: " + str(cur_tot_cap))
            tot += len(student_set)
            if verbose:
                print(tot)
        
    full_verification(all_routes, max_time, print_result = True)
    
    print("Contract buses used: " + str(contr_counts))
    print("Leftover original buses: " + str(cap_counts))

    tot = 0
    for bus in contr_counts:
        tot += bus[0]*bus[1]
    print("Total contract capacity used: " + str(tot))
    
    random.shuffle(all_routes)    
    #all_routes = sorted(all_routes, key = lambda x:x.occupants)
    print("Buses saved: " + str(mixed_loads(all_routes)))
        
    full_verification(all_routes, max_time, print_result = True)
    return all_routes
    
routes_returned = None
for i in range(10):
    routes_returned = main()
    saving = open(("C://Users//David//Documents//UCLA//SchoolBusResearch//" +
                   "mixedloadsstuff//magnet_only_3600s"+str(i)+".obj"), "wb")
    pickle.dump(routes_returned, saving)
    saving.close()