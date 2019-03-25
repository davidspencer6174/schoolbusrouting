import constants
import numpy as np
from itertools import chain

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

    def add_student(self, student):
        self.students.append(student)
        self.occupants += 1
    
    def updateBus(self, bus_cap):
        self.bus_size = bus_cap
    
    def updateSchoolsToVisit(self, student):
        self.schools_to_visit.add(student.school_ind)
        
    # Obtain the "center" of the route
    def findRouteCenter(self):
        
        lat = []
        long = []
        
        route_coords = constants.GEOCODES[constants.GEOCODES.index.isin(self.path)]
        for row in route_coords.iterrows(): 
            lat.append(row[1]['Lat'])
            long.append(row[1]['Long'])
        
        return (round(sum(lat)/float(len(lat)),6), round(sum(long)/float(len(long)),6))
    
    def schoollessPath(self):
        return list(filter(lambda x: x not in self.school_path, self.path))
    
    # Combine route
    def combineRoute(self, new_route):
        
        # Add new_route students into this route
        for new_stud in new_route.students:
            self.add_student(new_stud)

        # Perform routing with the new stops from the 'under-utilized' routes
        # Update path into route path 
        visited = list()
        index = 0
                
        total_indexes = sum([[self.school_path[-1]], self.schoollessPath(), new_route.schoollessPath()], [])
        route = [total_indexes[index]]

        # Create mini travel-time matrix and perform routing 
        dropoff_mat = [[0 for x in range(len(total_indexes))] for y in range(len(total_indexes))]
                
        for i in range(0, len(dropoff_mat)):
            for j in range(0, len(dropoff_mat[i])):
                dropoff_mat[i][j] = constants.TRAVEL_TIMES[total_indexes[i]][total_indexes[j]]  
                
        # Find shorest path through all the stops
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
        route.pop(0)
        
        # Update path and path_info
        self.path_info.append((constants.TRAVEL_TIMES[self.path[-1]][new_route.path[len(new_route.school_path)]], new_route.path_info[len(new_route.school_path)-1][1]))
        self.path_info.extend(new_route.path_info[2:])
        self.path = self.school_path + route
        
        # Update bus information
        for bus in constants.CAP_COUNTS:
            if bus[0] == new_route.bus_size:
                bus[1] += 1
        


