import numpy as np
import copy
import constants
from collections import defaultdict
from constraint_solver import solve_school_constraints

# School object 
class School:
    def __init__(self, tt_ind, cost_center, school_name):
        self.tt_ind = tt_ind
        self.cost_center = cost_center
        self.school_name = school_name
        self.age_type = constants.SCHOOLTYPE_MAP[tt_ind]

# Student object 
class Student:
    def __init__(self, tt_ind, school_ind):
        self.tt_ind = tt_ind
        self.school_ind = school_ind
        self.age_type = constants.SCHOOLTYPE_MAP[school_ind]
        self.time_on_bus = None
    
    # Calculate how much time a student spends on the bus
    def update_time_on_bus(self, current_route):
        school_ind = current_route.path.index(self.school_ind)
        stop_ind = current_route.path.index(self.tt_ind)
        new_time = current_route.path_info[school_ind:stop_ind]
        self.time_on_bus = round(sum([i for i,j in new_time]), 2)

# Route object  
class Route: 
    def __init__(self, school_path, stops_path, list_of_students):
        self.school_path = school_path
        self.stops_path = stops_path
        self.schools_to_visit = set()
        self.students_list = list()
        self.bus_size = 0
        self.pickup_students(list_of_students)

    # Update route variables 
    def update_bus(self, bus_cap):
        self.bus_size = bus_cap

    def update_contract_route_status(self):
        self.is_contract_route = True 

    # Get different info about route 
    def get_total_path(self):
        return self.school_path + self.stops_path

    def get_student_counts(self):
        count = np.sum([stop[2] for stop in self.stops_path])
        return count 

    # Pick up students  
    def add_student(self, student):
        self.students_list.append(student)
        self.schools_to_visit.add(student.school_ind)
    
    def pickup_students(self, list_of_students):
        for stop in self.stops_path:
            for stud in list_of_students:
                if stud.tt_ind == stop[0]:
                    self.add_student(stud)
                if len(self.students_list) >= self.get_student_counts():
                    break
    
    # Assign buses 
    def assign_bus_to_route(self):
        for bus_ind in range(len(constants.CAP_COUNTS)):
            bus = constants.CAP_COUNTS[bus_ind]
            MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[bus[0]])
            sum_stud_count = self.get_student_counts()

            if (sum_stud_count[0]/MOD_BUS[0])+(sum_stud_count[1]/MOD_BUS[1])+(sum_stud_count[2]/MOD_BUS[2]) <= 1:
                #mark the bus as taken
                bus[1] -= 1
                self.update_bus(bus[0])
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    constants.CAP_COUNTS.remove(bus)
                break

        if self.bus_size == None and not constants.CAP_COUNTS:
            self.assign_contract_route()
    
    # Assign contract bus 
    def assign_contract_route(self):
        print('CONTRACT BUS USED')
        self.update_contract_route_status()
        for bus_ind in range(len(constants.CONTRACT_CAP_COUNTS)):
            bus = constants.CONTRACT_CAP_COUNTS[bus_ind]
            MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[bus[0]])
            sum_stud_count = self.get_student_counts()

            if (sum_stud_count[0]/MOD_BUS[0])+(sum_stud_count[1]/MOD_BUS[1])+(sum_stud_count[2]/MOD_BUS[2]) <= 1:
                bus[1] += 1
                self.update_bus(bus[0])

    # TODO: Delete schools that do need to be visited 
    # Clean routes 
    def clean_routes(self):
        pass

# Clusters 
class Cluster:
    def __init__(self, schools_info, students_info):
        self.routes_list = list()
        self.school_path = list()
        self.schools_info_df = schools_info
        self.students_info_df = students_info
        self.students_list = list()
        self.schools_list = list()
        self.process_info()

    # insert csv information into objects
    def process_info(self):
        for _, row in self.students_info_df.iterrows():
            self.students_list += [Student(constants.CODES_INDS_MAP[str(round(row['Lat'],6)) + ";" + str(round(row['Long'],6))], row['tt_ind'])] 
        
        for _, row in self.schools_info_df.iterrows():
            self.schools_list += [School(row['tt_ind'], row['Cost_Center'], row['School_Name'])]
        
    # Time to travel through all schools
    def get_school_route_time(self):
        tot_time = 0
        if len(self.school_path) == 1:
            return tot_time
        else: 
            for idx, school in enumerate(self.school_path[1:]):
                tot_time += self.school_path[idx+1][1] + constants.DROPOFF_TIME[school]
            return tot_time 

    # Combine the clusters  
    def combine_clusters(self, new_cluster):
        combined_cluster = copy.deepcopy(self)
        combined_cluster.schools_info_df.append(new_cluster.schools_info_df)
        combined_cluster.students_info_df.append(new_cluster.students_info_df)

        # If the school constraints are met, then we can cluster together 
        if self.check_school_route_constraints():
            combined_cluster.process_info()
            combined_cluster.create_routes_for_cluster()

    # Create the routes for a given cluster using schools_set and stops_set
    def create_routes_for_cluster(self):
        from routing import route_cluster
        if self.check_school_route_constraints():
            routes_returned = route_cluster(self)
            
            if self.verify_routed_cluster(routes_returned):
                self.routes_list = routes_returned
            else:
                print("Routes generated are faulty")
        else:
            print("School constraints not met")
            return

    # Check for E/M/H relations
    # Use linear programming to check if routing school constraints are met 
    # TODO: Fix the school path when 
    def check_school_route_constraints(self):
        schools_age_type_set = set()
        for _, schools in self.schools_info_df.iterrows(): 
            schools_age_type_set.add(schools['School_type'])

        if len(schools_age_type_set) < 3:
            school_route = solve_school_constraints(self.schools_info_df)
            
            if school_route:
                if len(school_route) == 1:
                    self.school_path = [(school_route, 0)]
                else:
                    updated_school_path = [(school_route[0], 0)] + [(school, round(constants.TRAVEL_TIMES[school_route[idx-1]][school], 2)) for idx, school in enumerate(school_route[1:])]
                    self.school_path = updated_school_path
                return True
            else:
                return False
        else:
            print("Age types don't work")
            return False 

    # # Find the n closest school clusters using cluster 'center'
    # def find_closest_school_clusters(self):
    #     closest_clusters = list()
    #     return closest_clusters

    # Verification with csv files 
    def verify_routed_cluster(self, routes_returned):
        school_set_csv, school_set_route = set(), set()
        stop_dict_csv, stop_dict_route = defaultdict(int), defaultdict(int)

        for school in self.schools_list: 
            school_set_csv.add(school.tt_ind)

        for stud in self.students_list: 
            if stop_dict_csv.get(stud.tt_ind) is None:
                temp = [0] * 3 
                temp[stud.age_type] += 1
                stop_dict_csv[stud.tt_ind] = temp
            else:
                stop_dict_csv[stud.tt_ind][stud.age_type] += 1 

        for route in routes_returned: 
            [school_set_route.add(school) for school in route.school_path]

            for stop in route.stops_path:
                if stop_dict_route.get(stop[0]) is None:
                    stop_dict_route[stop[0]] = stop[2]
                else: 
                    stop_dict_route[stop[0]] = np.concatenate([stop_dict_route[stop[0]], stop[2]]).sum(axis=0)
                
        if school_set_csv == school_set_route and stop_dict_csv == stop_dict_route:
            return True 
        else:
            return False 

