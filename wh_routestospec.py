import constants
from locations import Route, Student

def wh_routes_to_spec(routes):
    returned_routes = list()
    for r in routes:
        new_r = convert_route_to_common(r)
        returned_routes.append(new_r)
    return returned_routes

def spec_to_wh_routes(routes):
    returned_routes = list()
    for r in routes:
        new_r = convert_route_from_common(r)
        returned_routes.append(new_r)
    return returned_routes

# Convert routes to common
def convert_route_to_common(route):
    list_of_stops = list()
    list_of_visited_schools = [sch[0] for sch in route.schools_path]
    for stop in route.stops_path:
        schools_at_stop = set()
        for stud in route.students_list:
            if stud.tt_ind == stop[0]:
                schools_at_stop.add(stud.school_ind)
        list_of_stops.append((stop[0], schools_at_stop))
    route_output = (list_of_stops, list_of_visited_schools, None)    
    return route_output
    
# A route plan is stored as a list of routes.
# A route is stored as a 3-tuple (list of stops, list of tt_inds for visited schools, bus capacity)
# A stop is stored as a 2-tuple (tt_ind, set of 2-tuples (school, age_type))
# Convert routes from common 
def convert_route_from_common(route):
    
    list_of_students = list()
    stops_path = list()
    schools_path = [(sch, 0) if idx == 0 else (sch, round(constants.TRAVEL_TIMES[route[1][idx-1]][sch],2)) for idx, sch in enumerate(route[1])]
    subset_phonebook = constants.PHONEBOOK[constants.PHONEBOOK['school_tt_ind'].isin([schools[0] for schools in schools_path])]
    list_of_students = list()

    for idx, stop in enumerate(route[0]):
                
        stop_subset_pb = subset_phonebook[subset_phonebook["stops_tt_ind"] == stop[0]]
        stud_stop_count = [0] * 3
        
        for idx_2, stud in stop_subset_pb.iterrows():
            stud_stop_count[constants.SCHOOLTYPE_MAP[stud.school_tt_ind]] += 1
            list_of_students.append(Student(stop[0], stud.school_tt_ind))
        
        if idx == 0:
            stops_path.append((stop[0], round(constants.TRAVEL_TIMES[schools_path[-1][0]][stop[0]],2), stud_stop_count))
        else:
            stops_path.append((stop[0], round(constants.TRAVEL_TIMES[route[0][idx-1][0]][stop[0]], 2), stud_stop_count))

    new_route = Route(schools_path, stops_path, None)
    new_route.add_students_manual(list_of_students)
    new_route.assign_bus_manual(route[2])
    new_route.clean_route()
    
    return new_route
