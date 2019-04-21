import constants
import numpy as np
import copy 

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
        self.time_on_bus = None

    # Calculate how much time a student spends on the bus
    def update_time_on_bus(self, stop, current_route):
        ind = current_route.get_schoolless_path().index(stop)
        newTime = sum([i for i,j in current_route.path_info[:ind+1]])
        self.time_on_bus = newTime 

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
        self.is_combined_route = False 
        self.is_contract_route = None 
        self.is_mixed_loads = False

    def __eq__(self, other): 
        if self.path == other.path and self.path_info == other.path_info and self.occupants == other.occupants:
            return True
        else:
            return False
            
    def get_route_length(self):
        return sum([i for i, j in self.path_info])

    def add_student(self, student):
        self.students.append(student)
        self.update_schools_to_visit(student)
        self.occupants += 1
   
    def update_schools_to_visit(self, student):
        self.schools_to_visit.add(student.school_ind)

    # Update different route status 
    def update_occupants(self):
        self.occupants = len(self.students)

    def update_combine_route_status(self):
        self.is_combined_route = True 

    def update_contract_route_status(self):
        self.is_contract_route = True 

    def update_mixed_loads_status(self):
        self.is_mixed_loads = True 

    def update_bus(self, bus_cap):
        self.bus_size = bus_cap
    
    # Obtain path without schools 
    def get_schoolless_path(self):
        return list(filter(lambda x: x not in self.school_path, self.path))
    
    # Check for mixed loads and update it on the object itself 
    def check_mixedload_status(self):
        school_set = set()
        for school in self.schools_to_visit:
            school_set.add(constants.SCHOOLTYPE_MAP[school])

        if len(school_set) != 1: 
            self.update_mixed_loads_status()

    # Clean routes and remove schools from path and path_info that will not be visited
    def clean_route(self):
    
        # If no cleaning needed
        new_school_path_info = list()
        if self.schools_to_visit == set(self.school_path):
            return 
        
        ori_school_path = copy.deepcopy(self.school_path)
        
        # Delete schools that do not need to be visited
        for index, school in enumerate(ori_school_path):
            if school not in self.schools_to_visit: 
                self.school_path.remove(school)
                self.path.remove(school)
        del self.path_info[0:len(ori_school_path)-1]
        
        for ind, school in enumerate(self.school_path):
            if ind == len(self.school_path)-1:
                new_school_path_info.append((round(constants.TRAVEL_TIMES[self.school_path[-1]][self.get_schoolless_path()[0]],2), self.path_info[0][1]))
            else:
                new_school_path_info.append((round(constants.TRAVEL_TIMES[school][self.school_path[ind+1]], 2), 0))

        self.path_info = new_school_path_info + self.path_info[1::]
                
    # assign a bus to a given route
    def assign_bus_to_route(self):
        # Assign buses to the routes according to num. of occupants
        # We have to use modified capacities mapping 
        for bus_ind in range(len(constants.CAP_COUNTS)):
             bus = constants.CAP_COUNTS[bus_ind]
             #found the smallest suitable bus
             if self.occupants <= constants.CAPACITY_MODIFIED_MAP[bus[0]][constants.SCHOOL_TYPE_INDEX]:
                 #mark the bus as taken
                 bus[1] -= 1
                 self.update_bus(bus[0])
                 #if all buses of this capacity are now taken, remove
                 #this capacity
                 if bus[1] == 0:
                     constants.CAP_COUNTS.remove(bus)
                 break 

    # TODO: WORK ON ASSIGNING CONTRACT BUS TO ROUTE
    # Assign contract bus to route 
    def assign_contract_bus_to_route(self): 
        self.update_contract_route_status()
        pass

    # Obtain the "center" of the route
    def find_route_center(self):
        lat = []
        long = []
        route_coords = constants.GEOCODES[constants.GEOCODES.index.isin(self.path)]
        for row in route_coords.iterrows(): 
            lat.append(row[1]['Lat'])
            long.append(row[1]['Long'])
        return (round(sum(lat)/float(len(lat)),6), round(sum(long)/float(len(long)),6))

    # Split route
    def split_route(self):

        total_students_list = copy.deepcopy(self.students)
        self.students = []
        split_route = copy.deepcopy(self)

        # Iterate through stops
        for i, stop in enumerate(self.get_schoolless_path()[::-1]):

            curr_idx = (i+1)*-1
            self.path_info[curr_idx] = (self.path_info[::-1][i][0], int((self.path_info[::-1][i][1])/2))
            split_route.path_info[curr_idx] = (self.path_info[::-1][i][0], split_route.path_info[::-1][i][1] - self.path_info[::-1][i][1])
            
            stud_list = list()
            for stud in total_students_list: 
                if stud.tt_ind == stop: 
                    stud_list.append(stud)
                    
            self.students.extend(stud_list[:self.path_info[curr_idx][1]])
            split_route.students.extend(stud_list[self.path_info[curr_idx][1]:])
                    
        self.update_occupants()
        self.assign_bus_to_route()
        split_route.update_occupants()
        split_route.assign_bus_to_route()
        
        return split_route

   # Obtain possible combined route time 
    def get_possible_combined_route_time(self, new_route):

        temp_route = copy.deepcopy(self)
        temp_route.combine_route(new_route)

        return sum([i for i, j in temp_route.path_info])
   
   # Combine route
    def combine_route(self, new_route):
        
        # Add new_route students into this route
        for new_stud in new_route.students:
            self.add_student(new_stud)

        # Perform routing with the new stops from the 'under-utilized' routes
        # Update path into route path 
        visited = list()
        index = 0
                
        total_indexes = sum([[self.school_path[-1]], self.get_schoolless_path(), new_route.get_schoolless_path()], [])
        route = [total_indexes[index]]

        # Create mini travel-time matrix and perform routing 
        dropoff_mat = [[0 for x in range(len(total_indexes))] for y in range(len(total_indexes))]
                
        for i in range(0, len(dropoff_mat)):
            for j in range(0, len(dropoff_mat[i])):
                dropoff_mat[i][j] = constants.TRAVEL_TIMES[total_indexes[i]][total_indexes[j]]  

        # Find shortest path through all the stops
        while len(route) < len(dropoff_mat):
            visited.append(index)
            temp = np.array(dropoff_mat[index])
            
            for ind in range(0, len(temp)):
                if ind in visited: 
                    temp[ind]=np.nan
                if ind == index:
                    temp[ind] = np.nan
        
            # Append the time taken to go from one stop to another in 
            # time taken and stop in route
            time_to_add = np.nanmin(temp)
            index = list(temp).index(time_to_add)
            route.append(total_indexes[index])
        
        # Remove school_path from route
        route = [x for x in route if x not in self.school_path]
        
        # Update path, path_info, and students time on bus
        new_path_info = list()
        base = self.school_path[-1]
        self.path = self.school_path + route

        for index, stop in enumerate(route):
            new_path_info.append((round(constants.TRAVEL_TIMES[base][stop], 2), len([x for x in self.students if x.tt_ind==stop])))
            base = stop

            for stud in self.students:
                stud.update_time_on_bus(stop, self)

        self.path_info = self.path_info[0:len(self.school_path)-1] + new_path_info
        
        # Update bus information - increment bus of discarded route back to cap_counts
        for bus in constants.CAP_COUNTS:
            if bus[0] == new_route.bus_size:
                bus[1] += 1

        self.assign_bus_to_route() 
        self.update_combine_route_status()
