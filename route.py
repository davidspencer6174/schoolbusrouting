import constants
import copy
import itertools
import numpy as np
from locations import Bus, School, Stop, Student

#Returns travel time from loc1 to loc2
def trav_time(loc1, loc2):
    return constants.TRAVEL_TIMES[loc1.tt_ind,
                                  loc2.tt_ind]
    
memoized_timechecks = dict()

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
        self.e_no_h = False
        self.h_no_e = False
        self.special_ed_students = set()
        #Tracks whether any student has a custom time limit
        self.student_time_limit = False
        #If no bus is assigned, the default capacity is infinite.
        #This is denoted by None.
        #Otherwise, this variable should hold the relevant Bus object.
        self.bus = None
        self.backups = dict()
        
    #Some approaches, e.g. Park+Kim mixed loads, are most efficiently
    #implemented with the ability to back up a route's data and
    #restore it.
    def backup(self, identifier):
        backup_obj = (copy.copy(self.stops), copy.copy(self.schools),
                      self.occupants, self.length,
                      self.max_time, copy.copy(self.valid_school_orderings),
                      self.special_ed_students, self.e_no_h,
                      self.h_no_e, self.student_time_limit,
                      copy.copy(self.special_ed_students))
        self.backups[identifier] = backup_obj
        
    def restore(self, identifier):
        (self.stops, self.schools, self.occupants,
         self.length, self.max_time, self.valid_school_orderings,
         self.special_ed_students, self.e_no_h, self.h_no_e,
         self.student_time_limit,
         self.special_ed_students) = self.backups[identifier]
        self.stops = copy.copy(self.stops)
        self.schools = copy.copy(self.schools)
        self.valid_school_orderings = copy.copy(self.valid_school_orderings)
        self.special_ed_students = copy.copy(self.special_ed_students)
        
    #Determine how many students have a particular need
    def count_needs(self, need):
        tot = 0
        for stud in self.special_ed_students:
            if stud.has_need(need):
                tot += 1
        return tot
        
    #Inserts a stop visit at position pos in the route.
    #The default position is the end.
    #Only check is feasibility of school addition.
    def add_stop(self, stop, pos = -1):
        if not self.add_school(stop.school):
            return False
        #Maintain the age type information
        if stop.e > 0 and stop.h == 0:
            self.e_no_h = True
        if stop.h > 0 and stop.e == 0:
            self.h_no_e = True
        for student in stop.special_ed_students:
            self.special_ed_students.add(student)
            if student.has_need("T"):
                self.student_time_limit = True
        if pos == -1:
            self.stops.append(stop)
            #Maintain the travel time field and occupants field
            self.occupants += stop.occs
            self.recompute_length()
            self.max_time = max(self.max_time,
                                constants.SLACK*trav_time(stop, stop.school))
            return True
        #Add the stop
        self.stops = self.stops[:pos] + [stop] + self.stops[pos:]
        #Maintain the relevant fields
        self.recompute_length()
        self.occupants += stop.occs
        self.max_time = max(self.max_time,
                            constants.SLACK*trav_time(stop, stop.school))
        return True
        
    def remove_stop(self, stop):
        self.stops.remove(stop)
        school = stop.school
        school_still_needed = False
        for other_stop in self.stops:
            if other_stop.school == school:
                school_still_needed = True
                break
        if not school_still_needed:
            self.schools = copy.copy(self.schools)
            self.schools.remove(school)
            #If there is nothing left, our length is 0
            #TODO: Figure out the right way to deal with this
            if len(self.schools) == 0:
                self.length = 0
                return
            self.enumerate_school_orderings()
        recheck_time = False
        for student in stop.special_ed_students:
            self.special_ed_students.remove(student)
            if student.has_need("T"):
                self.student_time_limit = False
                recheck_time = True
        if recheck_time:
            for stop_check in self.stops:
                for student in stop_check.special_ed_students:
                    if student.has_need("T"):
                        self.student_time_limit = True
        #Route will no longer be used in this case
        if len(self.stops) == 0:
            return
        self.recompute_length()
        self.recompute_occupants()
        self.recompute_type_info()
        self.recompute_maxtime()
        
    def get_route_length(self):
        return self.length
    
    #Performs an insertion of a stop such that the cost is minimized.
    #If the insertion is invalid in any respect, the insertion does
    #not occur and the function returns False.
    #Otherwise, performs the insertion and returns True.
    def insert_mincost(self, stop):
        self.backup("insert_mincost")
        if not self.add_school(stop.school):
            return False
        mach = self.count_needs("M")
        for stud in stop.special_ed_students:
            if stud.has_need("M"):
                mach += 1
            if stud.has_need("F"):
                #Two different stops that need to be the final stop
                if self.count_needs("F") > 0:
                    self.restore("insert_mincost")
                    return False
            if stud.has_need("T"):
                self.student_time_limit = True
        #Can't have too many students with machines
        #Do allow several students if they are all at
        #the same stop - seems unlikely though
        if mach > 2 and len(self.stops) > 1:
            self.restore("insert_mincost")
            return False
        if len(self.stops) > 0:
            best_cost = 100000
            best_ind = 0 
            #It is okay to insert this stop in the middle or the
            #beginning as long as no student on the stop needs
            #to be at the final stop.
            if len(self.stops) > 0 and stop.count_needs("F") == 0:
                best_cost = trav_time(stop, self.stops[0])
                for i in range(len(self.stops) - 1):
                    cost = (trav_time(self.stops[i], stop)
                            + trav_time(stop, self.stops[i + 1])
                            - trav_time(self.stops[i], self.stops[i + 1]))
                    if cost < best_cost:
                        best_cost = cost
                        best_ind = i + 1
            final_cost = (trav_time(self.stops[-1], stop) +
                          trav_time(stop, self.schools[0]) -
                          trav_time(self.stops[-1], self.schools[0]))
            #Can only insert at the end if no student already on
            #the route needs to be at the final stop.
            if final_cost < best_cost and self.count_needs("F") == 0:
                self.stops.append(stop)
            else:
                self.stops.insert(best_ind, stop)
        else:
            self.stops = [stop]
        for student in stop.special_ed_students:
            self.special_ed_students.add(student)
        #Maintain the age type information
        if stop.e > 0 and stop.h == 0:
            self.e_no_h = True
        if stop.h > 0 and stop.e == 0:
            self.h_no_e = True
        self.recompute_length()
        self.occupants += stop.occs
        self.recompute_maxtime()
        if (self.length > self.max_time or
            (self.student_time_limit and not self.check_special_times()) or
            self.bus != None and not self.bus.can_handle(self, True)):
            self.restore("insert_mincost")
            return False
        return True
    
    #Checks whether adding the school would leave
    #any valid orderings. If so, adds the school
    #and returns True.
    def add_school(self, school):
        if school not in self.schools:
            oldschools = self.schools
            self.schools = oldschools + [school]
            self.enumerate_school_orderings()
            if len(self.valid_school_orderings) == 0:
                self.schools = oldschools
                self.enumerate_school_orderings()
                return False
        return True

    #For students with special time limits, determine whether
    #they get to school on time.
    def check_special_times(self):
        for ind, stop in enumerate(self.stops):
            for stud in stop.students:
                if stud.has_need("T"):
                    time_limit = stud.need_value("T")
                    time_elapsed = 0
                    for i in range(ind + 1, len(self.stops)):
                        time_elapsed += trav_time(self.stops[i - 1], self.stops[i])
                        time_elapsed += self.stops[i].extra_time()
                    time_elapsed += trav_time(self.stops[-1], self.schools[0])
                    for i in range(0, len(self.schools)):
                        if self.schools[i] == stop.school:
                            break
                        time_elapsed += trav_time(self.schools[i], self.schools[i + 1])
                        time_elapsed += constants.SCHOOL_DROPOFF_TIME
                    if (time_elapsed > time_limit and
                        (stop != self.stops[-1] or stop.school != self.schools[0])):
                        return False
        return True
    
    #Outputs (valid, time) where valid is true if the belltimes
    #line up appropriately and time gives the amount of time
    #required to use this ordering.
    #valid will also be false if two of the schools are outside
    #of the acceptable maximum school distance.
    def time_check(self, school_perm):
        if tuple(school_perm) in memoized_timechecks:
            return memoized_timechecks[tuple(school_perm)]
        for school1 in school_perm:
            for school2 in school_perm:
                if trav_time(school1, school2) > constants.MAX_SCHOOL_DIST:
                    return (False, 0)
        #First, check for the morning routes
        time = 0
        mintime = school_perm[0].earliest_dropoff
        maxtime = school_perm[0].latest_dropoff
        for i in range(1, len(school_perm)):
            leg_time = trav_time(school_perm[i-1], school_perm[i])
            #If the shcools are different, need to add dropoff time
            #at the first school.
            if leg_time > 0:
                leg_time += constants.SCHOOL_DROPOFF_TIME
            mintime += leg_time
            maxtime += leg_time
            time += leg_time
            school_mintime = school_perm[i].earliest_dropoff
            school_maxtime = school_perm[i].latest_dropoff
            #Can't get to the school in time - give up
            if school_maxtime < mintime:
                memoized_timechecks[tuple(school_perm)] = (False, 0)
                return (False, 0)
            #Have to wait at the school - add the waiting time
            if school_mintime > maxtime:
                time += school_mintime - maxtime
            mintime = max(school_mintime, mintime)
            maxtime = min(school_maxtime, max(maxtime, mintime))
        memoized_timechecks[tuple(school_perm)] = (True, time)
        oldtime = time
        #Now, check for the afternoon routes.
        #We measure travel times for the morning routes, but we
        #should still check feasibility of the afternoon routes.
        time = 0
        mintime = school_perm[0].earliest_pickup
        maxtime = school_perm[0].latest_pickup
        for i in range(1, len(school_perm)):
            leg_time = trav_time(school_perm[i-1], school_perm[i])
            if leg_time > 0:
                leg_time += constants.SCHOOL_DROPOFF_TIME
            mintime += leg_time
            maxtime += leg_time
            time += leg_time
            school_mintime = school_perm[i].earliest_pickup
            school_maxtime = school_perm[i].latest_pickup
            #Can't get to the school in time - give up
            if school_maxtime < mintime:
                memoized_timechecks[tuple(school_perm)] = (False, 0)
                return (False, 0)
            #Have to wait at the school - add the waiting time
            if school_mintime > maxtime:
                time += school_mintime - maxtime
            mintime = max(school_mintime, mintime)
            maxtime = min(school_maxtime, max(maxtime, mintime))
        return (True, oldtime)
    
    def enumerate_school_orderings(self):
        self.valid_school_orderings = []
        for perm in itertools.permutations(self.schools):
            result = self.time_check(perm)
            if result[0]:
                self.valid_school_orderings.append([list(perm), result[1]])
    
    #Determining pickup time for wheelchair/lift students
    def sped_waiting_time(self):
        wheelchair_stops = set()
        lift_stops = set()
        for stud in self.special_ed_students:
            if stud.has_need("W"):
                wheelchair_stops.add(stud.stop)
            if stud.has_need("L"):
                lift_stops.add(stud.stop)
        lift_stops = lift_stops.difference(wheelchair_stops)
        return (constants.WHEELCHAIR_STOP_TIME*len(wheelchair_stops) +
                constants.LIFT_STOP_TIME*len(lift_stops))
       
    #If there is ever uncertainty about the length field, recompute length
    #Important: This reorders the schools to minimize the length.
    #As such, it may undo work by optimize_student_travel_times.
    def recompute_length(self):
        length = 0
        for i in range(len(self.stops) - 1):
            #Add time for wheelchair/lift
            length += self.stops[i].extra_time()
            length += trav_time(self.stops[i], self.stops[i+1])
        length += self.stops[-1].extra_time()
        best_length = 100000
        for possible_schools in self.valid_school_orderings:
            #Length is stop travel time plus stop to first school
            #plus school travel time
            if len(self.stops) == 0 or len(possible_schools[0]) == 0:
                print(self.stops)
                print(possible_schools[0])
                print("hmmmmmmmm")
            possible_length = (length +
                               trav_time(self.stops[-1], possible_schools[0][0]) +
                               possible_schools[1])
            if possible_length < best_length:
                best_length = possible_length
                self.schools = possible_schools[0]
        self.length = best_length
        return self.length
    
    #In cases where we don't want to look at school reorderings, just
    #recompute the length in the straightforward way.
    def recompute_length_naive(self):
        self.length = 0
        for i in range(0, len(self.stops) - 1):
            self.length += trav_time(self.stops[i], self.stops[i+1])
        self.length += trav_time(self.stops[-1], self.schools[0])
        for i in range(0, len(self.schools) - 1):
            self.length += trav_time(self.schools[i], self.schools[i+1])
            self.length += constants.SCHOOL_DROPOFF_TIME
        self.length += self.sped_waiting_time()
    
    def recompute_occupants(self):
        self.occupants = 0
        for stop in self.stops:
            self.occupants += stop.occs
            
    def recompute_type_info(self):
        self.e_no_h = False
        self.h_no_e = False
        for stop in self.stops:
            if stop.e > 0 and stop.h == 0:
                self.e_no_h = True
            if stop.h > 0 and stop.e == 0:
                self.h_no_e = True
            
    def recompute_maxtime(self):
        self.max_time = constants.MAX_TIME
        for stop in self.stops:
            self.max_time = max(self.max_time, constants.SLACK*
                                            trav_time(stop, stop.school))
        
    #Determines whether the route is feasible with
    #respect to constraints.
    def feasibility_check(self, verbose = False):
        #Recompute max time
        self.max_time = constants.MAX_TIME
        for s in self.stops:
            self.max_time = max(self.max_time,
                                constants.SLACK*trav_time(s, s.school))
        #Too long
        self.enumerate_school_orderings()
        self.recompute_length()
        if self.length > self.max_time:
            if verbose:
                print("Too long")
            return False
        if self.student_time_limit and not self.check_special_times():
            if verbose:
                print("Student's custom time limit is violated")
            return False
        #School not visited or mixed student types
        e_no_h = False
        h_no_e = False
        for s in self.stops:
            e_found = False
            h_found = False
            for student in s.students:
                if student.type == 'E':
                    e_found = True
                if student.type == 'H':
                    h_found = True
                if student.school not in self.schools:
                    if verbose:
                        print("School not visited")
                    return False
            if e_found and not h_found:
                e_no_h = True
            if h_found and not e_found:
                h_no_e = True
            if e_no_h and h_no_e:
                if verbose:
                    print("Student age types not feasible")
                return False
        #Too many students and there is a bus assigned and
        #there are multiple stops (sometimes, a single stop
        #has too many students for any bus to take, so we
        #assume that stop is handled alone)
        if (self.bus != None and
            not self.bus.can_handle(self, True) and
            len(self.stops) > 1):
            if verbose:
                print("Too full")
            return False
        #Now test mixed load bell time feasibility
        result = self.time_check(self.schools)
        if not result[0]:
            if verbose:
                print("Bell times contradict")
            return False
        #Next, check special ed feasibility.
        #Adult and individual supervision are already accounted for
        #in capacity check.
        #Modified travel time is already accounted for during
        #computation of max travel time.
        #Maximum number of machine students is 2
        machine_students = 0
        wheelchair_students = 0
        lift_needed = False
        for stud in self.special_ed_students:
            if stud.has_need("M"):
                machine_students += 1
            if stud.has_need("W"):
                wheelchair_students += 1
                lift_needed = True
            if stud.has_need("L"):
                lift_needed = True
            if stud.has_need("F"):
                if stud.stop != self.stops[-1]:
                    if verbose:
                        print("A student who needs to be the last stop is on an earlier stop")
                    return False
        if machine_students > 2 and self.stops > 1:
            if verbose:
                print("Too many students who need machines")
            return False
        if lift_needed and self.bus != None and not self.bus.lift:
            if verbose:
                print("Lift is needed, but the bus has no lift")
            return False
        if self.bus != None and wheelchair_students > self.bus.num_wheelchair_max:
            if verbose:
                print("Not enough wheelchair spots on bus")
                print(wheelchair_students)
                print(self.bus.num_wheelchair_max)
                print(self.bus.capacity)
            return False
        return True
    
    #Given a capacity, checks the age of the student and
    #stores the corresponding capacity
    def set_bus(self, bus):
        self.bus = bus
    
    #Accepts a bus array of length 3
    #The first number is the allowable number of elementary students
    #to assign, then  middle, then high
    #Returns whether it is valid to assign the bus to the route
    #to_add field allows checking whether it would be acceptable in
    #the presence of an addition.
    def is_acceptable(self, bus):
        cap = bus.capacity
        e = 0
        m = 0
        h = 0
        #Two types of supervisors that each take as much space as 2 H.
        #HCA/private nurses (different, but treated same) are for
        #individual students.
        #General supervisors can cover the whole bus.
        hca = 0
        sup_required = False
        for stop in self.stops:
            for stud in self.students:
                #Machine: takes up a full bench.
                if stud.has_need('M'):
                    h += 2
                    continue
                e += (stud.type == 'E')
                m += (stud.type == 'M')
                h += (stud.type == 'H')
                #HCA, private nurse, supervisor: takes up a full bench.
                if stud.has_need('I'):
                    hca += 1
                if stud.has_need('A'):
                    sup_required = True
        mod_caps = constants.CAPACITY_MODIFIED_MAP[cap]
        prop_occupied = (e/mod_caps[0] + m/mod_caps[1] + h/mod_caps[2] +
                         (hca+sup_required)*2/mod_caps[2])
        return (prop_occupied <= 1)
    
    #Check whether it is feasible to add more students of type
    #stud_type to the route given the bus
    def can_add(self, bus, stud_type, num_students = 1):
        to_add = [(stud_type == "E")*num_students,
                  (stud_type == "M")*num_students,
                  (stud_type == "H")*num_students]
        return self.is_acceptable(bus, to_add)
    
    #Returns a list of travel times from stop to
    #school, one per student.
    def student_travel_times(self):
        out = []
        for i in range(len(self.stops)):
            this_stop_time = 0
            for j in range(i, len(self.stops) - 1):
                this_stop_time += trav_time(self.stops[j], self.stops[j+1])
                #Add wheelchair/lift time
                this_stop_time += self.stops[j+1].extra_time()
            this_stop_time += trav_time(self.stops[-1], self.schools[0])
            j = 0
            while self.stops[i].school != self.schools[j]:
                this_stop_time += trav_time(self.schools[j], self.schools[j+1])
                #If they are different schools, need to include dropoff time.
                if trav_time(self.schools[j], self.schools[j+1]) > 0.1:
                    this_stop_time += constants.SCHOOL_DROPOFF_TIME
                j += 1
            for stud in range(self.stops[i].occs):
                out.append(this_stop_time)
        return out
    
    #Reorders the schools such that the mean student
    #travel time is minimized while still keeping
    #the total route length within allowable bounds.
    def optimize_student_travel_times(self):
        length = 0
        for i in range(len(self.stops) - 1):
            length += trav_time(self.stops[i], self.stops[i+1])
        best_trav_time = np.sum(self.student_travel_times())
        for possible_schools in self.valid_school_orderings:
            #Length is stop travel time plus stop to first school
            #plus school travel time
            possible_length = (length +
                               trav_time(self.stops[-1], possible_schools[0][0]) +
                               possible_schools[1])
            if possible_length <= self.max_time:
                tot_time = np.sum(self.student_travel_times())
                if tot_time < best_trav_time - .0000000001:
                    if constants.VERBOSE:
                        print("Saved " + str(best_trav_time-tot_time) +
                              " student travel time.")
                    best_trav_time = tot_time
                    self.schools = possible_schools[0]
        return best_trav_time