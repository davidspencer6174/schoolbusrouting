import numpy as np

#If true, informational lines will be printed
VERBOSE = True

#Identifies elementary, middle, and high school students
GRADES_TYPE_MAP = dict()
for i in range(0, 6):
    GRADES_TYPE_MAP[i] = 'E'
for i in range(6, 9):
    GRADES_TYPE_MAP[i] = 'M'
for i in range(9, 13):
    GRADES_TYPE_MAP[i] = 'H'
    
#For a stated capacity, make it easy to access the
#capacities for each age - elementary, middle, high
CAPACITY_MODIFIED_MAP = dict()
CAPACITY_MODIFIED_MAP[84] = [78, 65, 52]
CAPACITY_MODIFIED_MAP[65] = [65, 48, 42]
CAPACITY_MODIFIED_MAP[62] = [62, 45, 40]
CAPACITY_MODIFIED_MAP[42] = [40, 34, 27]
CAPACITY_MODIFIED_MAP[39] = [39, 35, 23]
CAPACITY_MODIFIED_MAP[34] = [34, 22, 22]
#Don't know whether these ones should be used
#Guessed on the numbers
CAPACITY_MODIFIED_MAP[71] = [71, 52, 45]
CAPACITY_MODIFIED_MAP[41] = [39, 33, 26]
CAPACITY_MODIFIED_MAP[33] = [33, 21, 21]
CAPACITY_MODIFIED_MAP[24] = [24, 17, 17]
CAPACITY_MODIFIED_MAP[17] = [17, 12, 12]
CAPACITY_MODIFIED_MAP[16] = [16, 11, 11]
#I guessed values for the contract buses, though
#I don't know whether these should actually
#be used
CAPACITY_MODIFIED_MAP[25] = [25, 16, 16]
CAPACITY_MODIFIED_MAP[12] = [12, 8, 8]
CAPACITY_MODIFIED_MAP[8] = [8, 5, 5]
    
#Assumed multiplier due to discrepancies betweeen OSRM estimated
#travel time and Google Maps estimated travel time
TT_MULT = 1.5

#If a student lives too far away from school, multiply the
#allowable route time by some slack to allow for still
#picking up other students.
SLACK = 1.1
 
#Load travel time matrix and multiply by TT_MULT
TRAVEL_TIMES = np.load("data//travel_time_matrix.npy")*TT_MULT

#Max allowable travel time in seconds
#MAX_TIME = 3600
MAX_TIME = 2700

#Seconds before belltime to determine valid arrival
#Valid arrival times are [belltime-EARLIEST, belltime-LATEST]
EARLIEST = 1800
LATEST = 600