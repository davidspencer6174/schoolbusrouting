import numpy as np
from setup import setup_buses
import pandas as pd
import pickle

#If true, informational lines will be printed
VERBOSE = True

#Max allowable travel time in seconds
#MAX_TIME = 3600
MAX_TIME = 2700

# Program types 
PROG_TYPES = ['P', 'X', 'M']

# School_type: 'elem', 'middle', 'high
SCHOOL_TYPE = 'elem'
BREAK_NUM = 5
OCCUPANTS_LIMIT = 10 
REMOVE_LOW_OCC = True 

# DBSCAN paramters
# Radius (km)
RADIUS = 2
MIN_PER_CLUSTER = 1


PREFIX = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
TRAVEL_TIMES = np.load(PREFIX + "travel_times.npy")
CAP_COUNTS = setup_buses(PREFIX+'dist_bus_capacities.csv')
GEOCODES = pd.read_csv(PREFIX+'all_geocodes.csv')

with open(PREFIX+'schools_codes_map','rb') as handle:
    SCHOOLS_CODES_MAP = pickle.load(handle)
with open(PREFIX+'stops_codes_map' ,'rb') as handle:
    STOPS_CODES_MAP = pickle.load(handle)
with open(PREFIX+'codes_inds_map' ,'rb') as handle:
    CODES_INDS_MAP = pickle.load(handle)
