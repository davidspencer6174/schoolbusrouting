import pickle
from ds_route import ds_route
from ds_locations import ds_School, ds_Student, ds_Stop
from ds_setup import setup_ds_students
import ds_constants

#Format for a ds_route plan: a list of formatted ds_routes
#Format for a ds_route: a 2-tuple containing a list of
#formatted stops and a list of school tt_inds.
#Format for a stop: 2-tuple (stop tt_ind, set of 2-tuples (school tt_ind, age_type))
def ds_route_to_spec(r):
    stops = []
    schools = []
    r_formatted = (stops, schools, r.unmodified_bus_capacity)
    #Set up stops
    prev_tt_ind = None
    stop_rep = (None, None)
    for stop in r.stops:
        if stop.tt_ind != prev_tt_ind:
            if stop_rep != (None, None):
                stops.append(stop_rep)
            prev_tt_ind = stop.tt_ind
            stop_rep = (stop.tt_ind, set())
        stop_rep[1].add(stop.school.tt_ind)
    stops.append(stop_rep)
    #Set up schools
    for school in r.schools:
        schools.append(school.tt_ind)
    stops.reverse()
    schools.reverse()
    return r_formatted

def ds_routes_to_spec(ds_routes):
    all_ds_routes = []
    for r in ds_routes:
        stops = []
        schools = []
        r_formatted = (stops, schools, r.unmodified_bus_capacity)
        #Set up stops
        prev_tt_ind = None
        stop_rep = (None, None)
        for stop in r.stops:
            if stop.tt_ind != prev_tt_ind:
                if stop_rep != (None, None):
                    stops.append(stop_rep)
                prev_tt_ind = stop.tt_ind
                stop_rep = (stop.tt_ind, set())
            stop_rep[1].add(stop.school.tt_ind)
        stops.append(stop_rep)
        #Set up schools
        for school in r.schools:
            schools.append(school.tt_ind)
        all_ds_routes.append(r_formatted)
        stops.reverse()
        schools.reverse()
    return all_ds_routes
  
def spec_to_ds_routes(spec_routes):
    
    resulting_ds_routes = []
    counter = 0
    for spec_r in spec_routes:
        # print(counter)
        counter += 1
        r = spec_to_ds_route(spec_r, ds_constants.STUDENTS, ds_constants.SCHOOLS_STUDENTS_MAP, ds_constants.ALL_SCHOOLS)
        resulting_ds_routes.append(r)
    return resulting_ds_routes

def spec_to_ds_route(spec_r, students, schools_students_map, all_schools):
    r = ds_route()
    #Information about stops
    for stop_group in spec_r[0][::-1]:
        for stop in stop_group[1]:
            #stop_stud_type = stop[1]
            for school in all_schools:
                if school.tt_ind == stop:
                    stop_school = school
            adding_stop = ds_Stop(stop_school)
            #r.stops.append(adding_stop)
            for student in students:
                if (student.school.tt_ind == stop_school.tt_ind and
                    student.tt_ind == stop_group[0]):
                        adding_stop.add_student(student)
            r.stops.append(adding_stop)
                    
    #School ordering
    for tt_ind in spec_r[1][::-1]:
        for school in all_schools:
            if tt_ind == school.tt_ind:
                r.schools.append(school)
                break
            
    #Assigned bus - may be None
    r.unmodified_bus_capacity = spec_r[2]
    
    #Now maintain invariants.
    r.recompute_length_naive()
    r.recompute_occupants()
    r.recompute_type_info()
    r.recompute_maxtime()
    
    return r