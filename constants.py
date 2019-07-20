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
    
#Maps grade types to indices in the range of the
#grade type map
TYPE_IND_MAP = dict()
TYPE_IND_MAP['E'] = 0
TYPE_IND_MAP['M'] = 1
TYPE_IND_MAP['H'] = 2
    
#For a stated capacity, make it easy to access the
#capacities for each age - elementary, middle, high
#This is populated by the setup_mod_caps function in setup
CAPACITY_MODIFIED_MAP = dict()
    
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
#MAX_TIME = 5500
#MAX_TIME = 4100
MAX_TIME = 3600
#MAX_TIME = 3300
#MAX_TIME = 3000

#Amount of time to drop off students at a school.
#Should be used in the computation of time travelling
#between schools.
SCHOOL_DROPOFF_TIME = 480.0

#Number of seconds to spend seeking an optimal bus assignment
#solution for a route before giving up and using the greedy method
BUS_SEARCH_TIME = 10.0

#Amount of time to stop for a wheelchair student and for a
#nonambulatory lift student who does not have a wheelchair
WHEELCHAIR_STOP_TIME = 300.0
LIFT_STOP_TIME = 120.0

#Farthest away a school can be from another school and
#still have its stops flagged as candidates to combine
MAX_SCHOOL_DIST = 947.033

#Cutoff below which a stop will not be accepted
#Goal is to reduce mean travel time
#EVALUATION_CUTOFF = -1000
EVALUATION_CUTOFF = -236.319

#Weights to determine value of a stop
#SCH_DIST_WEIGHT = 0.85
#STOP_DIST_WEIGHT = 0.2
SCH_DIST_WEIGHT = 1.18602
STOP_DIST_WEIGHT = .15649

#Seconds before belltime to determine valid arrival
#Valid arrival times are [belltime-EARLIEST, belltime-LATEST]
EARLIEST = 1800
LATEST = 600


#Constants to govern weighting of importance of
#distance from school in single-load initialization
#ALPHAS = [0.0, 0.1, 0.2, 0.3, 0.4]
ALPHAS = [0.0]