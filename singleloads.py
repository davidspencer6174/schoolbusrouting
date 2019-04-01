import constants
from route import Route
from utils import closest_pair, closest_addition

#WARNING: Empties set of route students
#Students is most efficient as a set
#Students must be nonempty
def single_route(route_students, school):
    #simply creates nearest neighbor route for now
    route = Route()
    #initialize route with just school
    route.add_location(school)
    #track max allowed time. there is a default value,
    #but if a student lives really far away, add
    #some slack.
    max_time = constants.MAX_TIME
    while len(route_students) > 0:
        to_add = closest_pair(route_students, [route.locations[0]])[0]
        max_time = max(max_time, constants.TRAVEL_TIMES[to_add.tt_ind,
                                                        school.tt_ind]*constants.SLACK)
        #add student to beginning of route
        route.add_location(to_add, pos = 0)
        route_students.remove(to_add)
    route.two_opt()  #perform two opt optimization procedure
    route.max_time = max_time
    return route


#student_set is the set of students attending the school
#school is the School object
    
def route_school(student_set, school):
    best_num_routes = 10000
    best_tot_time = 10000
    best_routes = None
    best_alpha = 0
    for alpha in constants.ALPHAS:
        school_students = list(student_set)
        school_students.sort(key = lambda s: -constants.TRAVEL_TIMES[s.tt_ind, school.tt_ind])
        route_set = set()
        while len(school_students) > 0:
            current_route = Route()
            current_route.add_location(school_students[0])
            current_route.add_location(school)
            age_type = school_students[0].type
            current_route.max_time = max(constants.MAX_TIME, constants.SLACK*
                                         constants.TRAVEL_TIMES[school_students[0].tt_ind, school.tt_ind])
            school_students.remove(school_students[0])
            while True:
                [student_to_add, foo, opt_dist] = closest_addition(current_route.locations,
                                              school_students,
                                              current_route.max_time*.8 - current_route.length,
                                              alpha,
                                              age_type)
                if student_to_add == None:
                    break
                if (current_route.length + opt_dist > current_route.max_time):
                    break
                if not current_route.add_student(student_to_add):
                    print(opt_dist)
                    print("bad")
                school_students.remove(student_to_add)
            route_set.add(current_route)
        tot_time = 0
        for route in route_set:
            tot_time += route.length
        if len(route_set) < best_num_routes or (len(route_set) == best_num_routes and
                                                tot_time < best_tot_time):
            best_num_routes = len(route_set)
            best_tot_time = tot_time
            
            best_routes = route_set
            best_alpha = alpha
    print("Best alpha is " + str(best_alpha))
    return best_routes   
        
        
        
    #school_students = list(student_set)
    #route_set = set()
    #while len(school_students) > 0:
        #Starts by creating a route with just one student
        #Ensures that students who are too far away from their
        #school still get a bus, though they will be alone on it
    #    init_student = closest_pair(school_students, [school])[0]
    #    current_students = set()
    #    current_students.add(init_student)
    #    age_type = init_student.type  #age group of student
        #Now all students will need to have the same age type
    #    school_students.remove(init_student)
    #    current_route = single_route(list(current_students), school)
        #keep track of max time allowed for this route
        
        #Now we continually attempt to add students
    #    while True:
            #all students are routed - terminate route
    #        if len(school_students) == 0:
    #            break
            #find the student nearest any student on the route
    #        student_to_add = closest_pair(current_students, school_students,
    #                                      age_type)[1]
    #        if student_to_add == None:  #no appropriately-aged student
    #            break
    #        current_students.add(student_to_add)
    #        new_route = single_route(list(current_students), school)
    #        #if the computed route is too long to add this student,
    #        #route is finished - don't use the new route
    #        if new_route.get_route_length() > new_route.max_time:
    #            current_students.remove(student_to_add)
    #            break
            #route is valid, so update current_route
    #        current_route = new_route
    #        school_students.remove(student_to_add)
    #    route_set.add(current_route)
    #return route_set