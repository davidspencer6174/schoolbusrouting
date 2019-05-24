import pickle
import numpy as np
import pandas as pd
from setup import setup_buses, setup_contract_buses
import constants

#If true, informational lines will be printed
VERBOSE = True
COMBINE_ROUTES = True
OUTPUT_TO_FILE = True 
CLEAN_ROUTE = True

#Max allowable travel time in seconds
MAX_TIME = 3600

# Program types
PROG_TYPES = ['P', 'X', 'M']

# School_type: 'elem', 'middle', 'high
BREAK_NUM = 4
UNDER_UTILIZED_COUNT = 10 
SCHOOL_TYPE = 'middle'
SCHOOL_CATEGORIES = ['elem', 'middle', 'high']
SCHOOL_TYPE_INDEX = 0
N_CLOSEST = 5 

# COMBINE_ROUTE PARAMETERS 
RELAX_TIME = MAX_TIME + 300 
INITIAL_LOW_OCC_ROUTES_COUNTS = 0

# DBSCAN paramters
RADIUS = 1200
RADIUS_STUDENT = 1400
MIN_SAMPLES = 1

# Agglo parameters 
NUM_CLUSTERS_AGGLO = 140 

# MODIFIED BUS CAPACITES 
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

def REFRESH_STATS():
    constants.CAP_COUNTS, constants.CONTRACT_CAP_COUNTS = setup_buses(PREFIX+'dist_bus_capacities.csv')

PREFIX = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Willy_Data/mixed_load_data/"
TRAVEL_TIMES = (np.load(PREFIX + "travel_times.npy")*1.5)
CAP_COUNTS, CONTRACT_CAP_COUNTS = setup_buses(PREFIX+'dist_bus_capacities.csv')
GEOCODES = pd.read_csv(PREFIX+'all_geocodes.csv')

# For dropoff/bell times purposes
SCHOOL_ROUTE = dict()
SCHOOL_ROUTE_TIME = dict()
DROPOFF_TIME = dict()

# For verification purposes 
STUDENT_CLUSTER_COUNTER = dict()
STUDENT_STOP_COUNTER = dict()

DF_TRAVEL_TIMES = pd.DataFrame(data=np.transpose(constants.TRAVEL_TIMES))

with open(PREFIX+'schools_codes_map', 'rb') as handle:
    SCHOOLS_CODES_MAP = pickle.load(handle)
with open(PREFIX+'stops_codes_map', 'rb') as handle:
    STOPS_CODES_MAP = pickle.load(handle)
with open(PREFIX+'codes_inds_map', 'rb') as handle:
    CODES_INDS_MAP = pickle.load(handle)
with open(PREFIX+'schooltypes_map', 'rb') as handle:
    SCHOOLTYPE_MAP = pickle.load(handle)
with open(PREFIX+'schoolnames_map.pickle', 'rb') as handle:
    SCHOOLNAME_MAP = pickle.load(handle)

PHONEBOOK = pd.DataFrame()

