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
    
#Assumed multiplier due to discrepancies betweeen OSRM estimated
#travel time and Google Maps estimated travel time
TT_MULT = 1.5
 
#Load travel time matrix and multiply by TT_MULT
TRAVEL_TIMES = np.load("data//travel_time_matrix.npy")*TT_MULT

#Max allowable travel time in seconds
#MAX_TIME = 3600
MAX_TIME = 2700

#Seconds before belltime to determine valid arrival
#Valid arrival times are [belltime-EARLIEST, belltime-LATEST]
EARLIEST = 1800
LATEST = 600