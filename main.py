import constants
from locations import Student
from mixedloads import mixed_loads
import pickle
import random
from setup import setup_buses, setup_students
from singleloads import route_school
from validation import full_verification

def main():
    #prefix = "C://Users//David//Documents//UCLA//SchoolBusResearch//data//csvs//"
    prefix = "data//"
    output = setup_students([prefix+'phonebook_parta.csv',
                             prefix+'phonebook_partb.csv'],
                             prefix+'all_geocodes.csv',
                             prefix+'stop_geocodes_fixed.csv',
                             prefix+'school_geocodes_fixed.csv',
                             prefix+'bell_times.csv')
    students = output[0]
    schools_students_map = output[1]
    schools_inds_map = output[2]
    cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
    #So far, we are using 0 of each contract size.
    #This will get incremented when the schools get routed.
    #contr_counts = [[8, 0], [12, 0], [25, 0], [39, 0], [65, 0]]
    #This option only allows using the larger buses -
    #I think this is preferred by LAUSD
    contr_counts = [[39, 0], [65, 0]]
    if constants.VERBOSE:
        print(len(students))
        print(len(schools_students_map))
        print(cap_counts)
    tot_cap = 0
    for bus in cap_counts:
        tot_cap += bus[0]*bus[1]
            
    if constants.VERBOSE:
        print("Total capacity: " + str(tot_cap))

    tot = 0
    all_routes = list()
    
    schoolsstudents = schools_students_map.items()
    schoolsstudents = sorted(schoolsstudents, key = lambda x:-len(x[1]))
    for schoolsetpair in schoolsstudents:
        student_set = schoolsetpair[1]
        school_to_route = None
        for student in student_set:  #get the school from a student
            school_to_route = student.school
            break
        for route in route_school(student_set, cap_counts, contr_counts,
                                  school_to_route):
            all_routes.append(route)
        if len(student_set) > 0:
            if constants.VERBOSE:
                print("Routed school of size " + str(len(student_set)))
            cur_tot_cap = 0
            for bus in cap_counts:
                cur_tot_cap += bus[0]*bus[1]
            if constants.VERBOSE:
                print("Remaining capacity: " + str(cur_tot_cap))
            tot += len(student_set)
            if constants.VERBOSE:
                print(tot)
     
    
    full_verification(all_routes, print_result = True)
    
    print("Contract buses used: " + str(contr_counts))
    print("Leftover original buses: " + str(cap_counts))

    tot = 0
    for bus in contr_counts:
        tot += bus[0]*bus[1]
    print("Total contract capacity used: " + str(tot))
    
    for route in all_routes:
        types = set()
        for loc in route.locations:
            if isinstance(loc, Student):
                types.add(loc.type)
            if len(types) > 1:
                print("Bad")
                print(types)
    
    random.shuffle(all_routes)    
    all_routes = sorted(all_routes, key = lambda x:x.occupants)
    print("Buses saved: " + str(mixed_loads(all_routes)))
        
    full_verification(all_routes, print_result = True)
    return all_routes
    
routes_returned = None
for i in range(0,10):
    routes_returned = main()
    saving = open(("output//slack_for_faraway"+str(i)+".obj"), "wb")
    pickle.dump(routes_returned, saving)
    saving.close()