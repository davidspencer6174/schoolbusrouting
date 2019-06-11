import numpy as np 
from utils import unpack_routes
from collections import defaultdict
import constants 

def diagnostics(clustered_routes):
    
    routes = unpack_routes(clustered_routes)
    check_counts(routes)
    verify_routes(routes)
    
    # With most schools visited and most stops visited 
    schools_visited_dict = defaultdict(list) 
    stops_visited_dict = defaultdict(list)
    for route in routes: 
        schools_visited_dict[len(route.schools_path)].append(route)
        stops_visited_dict[len(route.stops_path)].append(route)
        
def check_counts(routes):
    tot_stud_counts = 0 
    df_school_student_counts = defaultdict(int)
    route_school_student_counts = defaultdict(list)
    
    for route in routes: 
        tot_stud_counts += len(route.students_list)
        
        for stud in route.students_list: 
            if route_school_student_counts.get(stud.school_ind) is None:
                route_school_student_counts[stud.school_ind] = 1
            else: 
                route_school_student_counts[stud.school_ind] += 1
        
    for school in np.sort(constants.PHONEBOOK.school_tt_ind.unique()):
        df_school_student_counts[school] = len(constants.PHONEBOOK[constants.PHONEBOOK["school_tt_ind"]==school])
        
    if tot_stud_counts == constants.PHONEBOOK.shape[0] and \
    sum(df_school_student_counts.values()) == sum(route_school_student_counts.values()):
        print("Counts match up")
        print("Number of students routed: " + str(sum(df_school_student_counts.values())))
        
    else:
        print("ERROR: counts do not match up")
    
def verify_routes(routes):
    routes_too_long = list()
    
    for route in routes:
        if route.get_route_length() > constants.MAX_TIME and \
        len(route.stops_path) > 1:
            
            print("ERROR: Route is too long")
            print(route.get_route_length())
            print('-------------------')
            routes_too_long.append(route)
            
    return routes_too_long

        # TODO: deal with buses 
#        if not check_bus_cap(route):
#            routes_over_cap.append(route)

#def check_bus_cap(route):
#    route_stud_counts = (np.array([j[2] for j in route.stops_path])).sum(axis=0)
#    MOD_BUS = (constants.CAPACITY_MODIFIED_MAP[max(constants.CAP_COUNTS.keys())])
#    pass
    