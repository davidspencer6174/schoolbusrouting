from route import Route
from locations import School, Student, Stop
import pickle
from setup import setup_students

to_spec_types = dict([['E', 0], ['M', 1], ['H', 2]])
from_spec_types = dict([[0, 'E'], [1, 'M'], [2, 'H']])

#Format for a route plan: a list of formatted routes
#Format for a route: a 2-tuple containing a list of
#formatted stops and a list of school tt_inds.
#Format for a stop: 2-tuple (stop tt_ind, set of 2-tuples (school tt_ind, age_type))

def dsroutes_to_spec(routes, filepath):
    all_routes = []
    for r in routes:
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
            stop_rep[1].add((stop.school.tt_ind, to_spec_types[stop.type]))
        stops.append(stop_rep)
        #Set up schools
        for school in r.schools:
            schools.append(school.tt_ind)
        all_routes.append(r_formatted)
    saving = open(filepath, 'wb')
    pickle.dump(all_routes, saving)
    saving.close()
  
def spec_to_dsroute(spec_r, students, schools_students_map, all_schools):
    r = Route()
    
    #First bring in all of the information
    
    #Information about stops
    for stop_group in spec_r[0]:
        for stop in stop_group[1]:
            stop_stud_type = from_spec_types[stop[1]]
            #stop_stud_type = stop[1]
            for school in all_schools:
                if school.tt_ind == stop[0]:
                    stop_school = school
            adding_stop = Stop(stop_school, stop_stud_type)
            r.stops.append(adding_stop)
            for student in students:
                if (student.school.tt_ind == stop_school.tt_ind and
                    student.type == stop_stud_type and
                    student.tt_ind == stop_group[0]):
                    adding_stop.add_student(student)
                    
    #School ordering
    for tt_ind in spec_r[1]:
        for school in all_schools:
            if tt_ind == school.tt_ind:
                r.schools.append(school)
                break
            
    
    #Assigned bus - may be None
    r.unmodified_bus_capacity = spec_r[2]
    
    #Now maintain invariants.
    r.recompute_length_naive()
    r.recompute_occupants()
    r.recompute_maxtime()
    
    return r
    
def spec_to_dsroutes(filepath):
    loading = open(filepath, 'rb')
    spec_routes = pickle.load(loading)
    loading.close()
    
    prefix = "data//"
    output = setup_students([prefix+'phonebook_parta.csv',
                             prefix+'phonebook_partb.csv'],
                             prefix+'all_geocodes.csv',
                             prefix+'stop_geocodes_fixed.csv',
                             prefix+'school_geocodes_fixed.csv',
                             prefix+'bell_times.csv')
    students = output[0]
    schools_students_map = output[1]
    all_schools = output[2]
    
    resulting_routes = []
    counter = 0
    for spec_r in spec_routes:
        print(counter)
        counter += 1
        r = spec_to_dsroute(spec_r, students, schools_students_map, all_schools)
        resulting_routes.append(r)
        
    return resulting_routes

#loading = open("output//test_transfer_backup.obj", "rb")
#testing_routes = pickle.load(loading)
#loading.close()
#dsroutes_to_spec(testing_routes, "testing_routes_save.obj")

#recovered_routes = spec_to_dsroutes("testing_routes_save.obj")

willy_routes = spec_to_dsroutes('willy_routes.obj')
#my_routes = spec_to_dsroutes('tmp_specdroutes.obj')