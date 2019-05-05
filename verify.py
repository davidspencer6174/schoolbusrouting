import numpy as np 
import pandas as pd 
import constants 
from collections import defaultdict

# Go through routes and verify route
def verify_routes(routes_returned): 

    student_stop_count_checker = defaultdict(int) 
    print("Verifying routes...")

    for i in range(0, len(routes_returned)):
    
        stops_set = set()
        for route in routes_returned[i]:
            stops_set.update(set(route.get_schoolless_path()))
            if route.verify_route():
                pass 
            else:
                print("ERROR -- Route doens't work")

            for stud in route.students: 
                student_stop_count_checker[stud.tt_ind] += 1

        if stops_set != constants.STUDENT_CLUSTER_COUNTER[i]:
            print("ERROR: STOPS NOT MATCHED")

    if student_stop_count_checker != constants.STUDENT_STOP_COUNTER:
        print("ERROR: Student counts at stops aren't matched")


    print("Verification complete...")



