import constants
from locations import Student

#Verifies the routes without relying on the fields of the
#routes, i.e. computes travel time and occupants from
#scratch.
def full_verification(routes, print_result = False):
    valid = True
    students = set()
    for route in routes:
        #Note: some routes which exceed max length just pick up
        #one student and drop them off at school. These shouldn't
        #be considered invalid.
        if not route.feasibility_check() and route.occupants > 1:
            print("Ordinary check failed")
            return False
        time = 0
        locations = route.locations
        max_time = constants.MAX_TIME
        for i in range(len(locations) - 1):
            time += constants.TRAVEL_TIMES[locations[i].tt_ind,
                                           locations[i+1].tt_ind]
            if isinstance(locations[i], Student):
                school_dist = constants.TRAVEL_TIMES[locations[i].tt_ind,
                                                     locations[i].school.tt_ind]
                max_time = max(max_time, school_dist*constants.SLACK)
                if locations[i].type != locations[0].type:
                    valid = False
                    print("Student ages on a bus differ")
        if time > max_time and route.occupants > 1:
            valid = False
            print("Max time violated")
        for loc_ind in range(len(locations)):
            loc = locations[loc_ind]
            if isinstance(loc, Student):
                students.add(loc)
                if loc.school not in locations[loc_ind+1:]:
                    print("Did not visit student's school")
                    valid = False
    if print_result:
        print("Completed route verification process.")
    if valid:
        if print_result:
            print(str(len(students)) + " students successfully routed.")
        return True    
    if print_result:
        print("At least one invalid route was found.")
    return False