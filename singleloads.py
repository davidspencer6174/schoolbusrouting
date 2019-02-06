import constants
from route import Route
from utils import closest_pair

#WARNING: Empties set of route students
#Students is most efficient as a set
#Students must be nonempty
def single_route(route_students, school):
    #simply creates nearest neighbor route for now
    route = Route()
    #initialize route with just school
    route.add_location(school)
    while len(route_students) > 0:
        to_add = closest_pair(route_students, [route.locations[0]])[0]
        #add student to beginning of route
        route.add_location(to_add, pos = 0)
        route_students.remove(to_add)
    route.two_opt()  #perform two opt optimization procedure
    return route


#student_set is the set of students attending the school
#cap_counts is a list of [bus capacity, count] pairs sorted by capacity
#contr_counts is a list of contract buses consumed
#school is the School object
    
def route_school(student_set, cap_counts, contr_counts, school):
    
    school_students = list(student_set)
    route_set = set()
    while len(school_students) > 0:
        #Starts by creating a route with just one student
        #Ensures that students who are too far away from their
        #school still get a bus, though they will be alone on it
        init_student = closest_pair(school_students, [school])[0]
        current_students = set()
        current_students.add(init_student)
        age_type = init_student.type  #age group of student
        #Now all students will need to have the same age type
        school_students.remove(init_student)
        current_route = single_route(list(current_students), school)
        
        #Now we continually attempt to add students
        while True:
            #used all district buses and no contract bus is large enough
            #for another student - terminate route
            if (len(cap_counts) == 0 and
                not current_route.can_add(contr_counts[-1][0])):
                break
            #there are still district buses but
            #no district bus of large enough capacity exists to
            #take more students - terminate route
            if (len(cap_counts) > 0 and
                not current_route.can_add(cap_counts[-1][0])):
                break
            #all students are routed - terminate route
            if len(school_students) == 0:
                break
            #find the student nearest any student on the route
            student_to_add = closest_pair(current_students, school_students,
                                          age_type)[1]
            if student_to_add == None:  #no appropriately-aged student
                break
            current_students.add(student_to_add)
            new_route = single_route(list(current_students), school)
            #if the computed route is too long to add this student,
            #route is finished - don't use the new route
            if new_route.get_route_length() > constants.MAX_TIME:
                current_students.remove(student_to_add)
                break
            #route is valid, so update current_route
            current_route = new_route
            school_students.remove(student_to_add)
        route_set.add(current_route)
        #Look for the district bus that can accommodate the route
        for bus_ind in range(len(cap_counts)):
            bus = cap_counts[bus_ind]
            #found the smallest suitable bus
            if current_route.is_acceptable(bus[0]):
                #mark the bus as taken
                bus[1] -= 1
                #Update the route to know the bus capacity
                current_route.set_capacity(bus[0])
                #if all buses of this capacity are now taken, remove
                #this capacity
                if bus[1] == 0:
                    cap_counts.remove(bus)
                break
        #If all district buses have been used, use a contract bus.
        if len(cap_counts) == 0:
            for bus_ind in range(len(contr_counts)):
                bus = contr_counts[bus_ind]
                if current_route.is_acceptable(bus[0]):
                    bus[1] += 1
                    current_route.set_capacity(bus[0])
                    break
    return route_set