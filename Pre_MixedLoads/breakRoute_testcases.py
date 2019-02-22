school_route = [10776, 10494, 10868, 10501]

current_time = 217.1
times_required = [3.5, 26.4, 63.1, 36.6, 117.7, 99.1, 215.8, 0 ]
max_time = 3600

current_time = 30 
stud_route = [800, 5106, 2712, 9027, 8439, 5651, 6322, 6614]
times_required = [20, 40, 10, 80, 30, 20, 10, 0]
max_time = 100

def breakRoutes(dropoff_time, school_route, stud_route, times_required):
    current_time = dropoff_time
    time_index = 0 
    route_list = list()
    partial_route = list()
    for stop in stud_route:
        partial_route.extend([stop])
        if current_time + times_required[time_index] >= max_time:
            route_list.append(partial_route)
            partial_route = list()
            current_time = dropoff_time
        else:
            current_time += times_required[time_index]
        time_index += 1 
    route_list.append(partial_route)
    
    final_list = list()
    for route in route_list:
        final_list.append(school_route + route)
    return final_list


test_1 = breakRoutes(current_time, stud_route, times_required)
