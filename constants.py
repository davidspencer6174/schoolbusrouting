import numpy as np

#If true, informational lines will be printed
VERBOSE = True

GEOCODES = None

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
 
TRAVEL_TIMES = None

#Max allowable travel time in seconds
MAX_TIME = 3600

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

#Seconds before/after belltime to determine valid arrival
#Valid AM arrival times are [starttime - EARLIEST_AM, starttime - LATEST_AM]
EARLIEST_AM = 1800
LATEST_AM = 600
#Valid PM arrival times are [endtime + EARLIEST_PM, endtime + LATEST_PM]
EARLIEST_PM = 600
LATEST_PM = 1200

#Determines the relative importance of number of routes and
#mean student travel time.
#.01 means that .01 minutes of mean travel time is as important
#as a reduction of one route.
MSTT_WEIGHT = .01

#Denotes approximately how much time to spend on each segment
MINUTES_PER_SEGMENT = None

#Constants to govern weighting of importance of
#distance from school in single-load initialization
#ALPHAS = [0.0, 0.1, 0.2, 0.3, 0.4]
ALPHAS = [0.0]

#Option to explicitly allow or forbit a pair of schools
#regardless of the distance between them.
ALLOWED_SCHOOL_PAIRS = set()
FORBIDDEN_SCHOOL_PAIRS = set()

#List of filenames to be read
FILENAMES = [None for i in range(9)]

SPEC_TEXT = []
SPEC_TEXT.append("""Comma separated value file with seven columns, which are labeled in a header row.
                 
Student ID: a unique identifier for students
Latitude: Student's stop latitude
Longitude: Student's stop longitude
Grade: Student's grade level. The program uses this to determine whether to treat the student as elementary, middle, or high. It expects 0-12 inclusive.
Needs: Only processed for SP students. List of needs separated by semicolons. W = needs a wheelchair, L = needs a lift bus but not a wheelchair space, A = adult supervision, I = HCA or private nurse, M = machine such as oxygen or suctioning, F = needs to be the final stop on the route, and T30 = 30 minute max ride time (the 30 can be changed).
RG/SP: Determines whether the student is special ed or not
Cost Center: Cost center identifier to associate with the school information""")

SPEC_TEXT.append("""Comma separated value file with six required columns and four optional columns, which are labeled in a header row.

Cost Center: Cost center identifier as in the student information encoding
School Name: Name of the school (for printout purposes)
Start: Start time in format x:xxAM or xx:xxAM
End: End time in format x:xxPM or xx:xxPM
Latitude: School latitude
Longitude: School longitude
Optional columns: If four more columns are provided, these are used as custom time windows for pickup and dropoff at that school. In order, these are the earliest time at which students can be dropped off, the latest, the earliest time at which they can be picked up, and the latest. By default, these windows are [start_time-30, start_time-10] and [end_time+10, end_time+20].""")

SPEC_TEXT.append("""Comma separated value file with five columns, which have brief descriptions in a header row.

Bus Number: Not required by the program, but it seems useful to have this for record-keeping.
Capacity (walk-on): the capacity of the bus, not taking into account overbooking, absenteeism, or student ages
Lift? (Y/N): Whether the bus has a lift, which the program uses to exclude lift buses when routing for magnet students
Min # Wheelchair Spots and Max # Wheelchair Spots: Only used if the program is told to assign buses for special ed routes, which is disabled by default.""")

SPEC_TEXT.append("""Two-dimensional matrix (serialized by Python's numpy library) where, for instance, the entry at position [0, 1] is the estimated number of seconds required to travel from geocode 0 to geocode 1 (ordered by the list in 'Geocodes for map data'). The matrix was generated by the Open Source Routing Machine; I multiply it by 1.5 within the program (constants.TT_MULT in the Python program) to be more consistent with the times that Google Maps gives. It isn't necessary to update this information every year, since the program "snaps" unknown geocodes onto the nearest known geocode. However, the times will become more inaccurate over the years, so occasional updates would be useful.""")

SPEC_TEXT.append("""Semicolon separated value file that lists latitude-longitude pairs mapped in the 'Map data' file, in which each row has the format latitude;longitude and there is no header row.""")

SPEC_TEXT.append("""Comma separated value file with four columns, which are labeled in a header row.

The first column is the bus capacity as given in the bus information file. The second, third, and fourth columns are the capacities if the bus is to be filled with elementary, middle, and high school students respectively.""")

SPEC_TEXT.append("""Comma separated value file giving various program parameters. The first row is a header row, the second row contains chosen parameters to use for magnet routing, and the third row contains parameters to use for special ed.

Max Travel Time (min): The maximum travel time that students can typically be required to travel.
Assumed Traffic Multiplier: The max travel times are divided by this multiplier to account for traffic.
Weighting of importance of mean student travel time (min) relative to number of routes: The program uses this number to quantify the tradeoff between travel times and number of routes. If this number is .03, this means that the mean travel time would have to decrease by .03 minutes to justify increasing the number of routes by 1.
Number of minutes to spend searching for solutions: A guideline for the program's execution time. It will run until it reaches the time limit for that part, finish its current routing attempt, and then return (so, it will take longer than the time limit, potentially up to an extra half hour or so for the magnet routing on most computers).
Slack ratio: If d is the distance from a student's stop to their school and s is the slack ratio, their maximum allowed travel time is the maximum of the default value and s*d. For example, if this value is 1.1, then a student whose stop is 60 minutes from their school is permitted by the program to travel for up to 66 minutes, even if the standard allowed time is 60 minutes. This should be at least 1.0.
Maximum allowed distance between schools (min): the default travel time within which the program will consider putting schools on the same route.""")

SPEC_TEXT.append("""The comma separated value files forbidden_school_pairs.csv and allowed_school_pairs.csv allow for exceptions to the maximum school distance parameter. If two schools are farther than the maximum school distance but their names appear in allowed_school_pairs.csv (with the format school_name_1,school_name_2), the program will consider routes which pair them. Similarly, if two schools are within the maximum school distance but their names appear in forbidden_school_pairs.csv, the program will not make any routes that pair them.""")

SPEC_TEXT.append("""The comma separated value files forbidden_school_pairs.csv and allowed_school_pairs.csv allow for exceptions to the maximum school distance parameter. If two schools are farther than the maximum school distance but their names appear in allowed_school_pairs.csv (with the format school_name_1,school_name_2), the program will consider routes which pair them. Similarly, if two schools are within the maximum school distance but their names appear in forbidden_school_pairs.csv, the program will not make any routes that pair them.""")

#SPEC_TEXT = ["test1", "test2", "test3", "test4", "test5", "test6", "test7",
#             "test8", "test9"]