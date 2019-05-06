import numpy as np 
import pandas as pd 
import constants 
from collections import defaultdict

# Go through routes and verify route
def verify_routes(routes_returned): 

    # Initialize variables 
    student_stop_count_checker = defaultdict(int) 
    student_stop_count_checker_path_info = defaultdict(int) 
    print("Verifying routes...")

    for i in range(0, len(routes_returned)):
    
        stops_set = set()
        for route in routes_returned[i]:

            # Record stops visited using route.path 
            stops_set.update(set(route.get_schoolless_path()))

            # Verify each route 
            if route.verify_route():
                pass 
            else:
                print("ERROR -- Route doens't work")

            # Record counts of students at every stop using embedded student objects 
            for stud in route.students: 
                student_stop_count_checker[stud.tt_ind] += 1

            # Record counts of students at every stop using route.path / route.path_info 
            if len(route.get_schoolless_path()) == 1: 
                student_stop_count_checker_path_info[route.get_schoolless_path()[0]] += sum(route.path_info[-1][1])
            else:
                for idx, stop in enumerate(route.get_schoolless_path()[::-1]):
                    student_stop_count_checker_path_info[stop] += sum(route.path_info[-idx-1][1])

        if stops_set != constants.STUDENT_CLUSTER_COUNTER[i]:
            print("ERROR: STOPS NOT MATCHED")

    # Use embedded student objects to check student counts at every stop
    if student_stop_count_checker != constants.STUDENT_STOP_COUNTER:
        print("ERROR: Student counts at stops aren't matched (based on student objects)")

    # Use path info to check student counts at every stop 
    if student_stop_count_checker_path_info != constants.STUDENT_STOP_COUNTER:
        print("ERROR: Student counts at stops aren't matched (based on path info)")
 
    print("Verification complete...")



