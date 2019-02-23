# TEST CASES
current_time = 0
school_route = [9507]
stud_route = [7492, 8324]
times_required = [1635.5, 480.1]




def breakRoutes(dropoff_time, school_route, stud_route, times_required):
    
    route_list = list()
    time_list = list()
    
    temp_route = list()
    temp_times = list()
    
    for index, time in enumerate(times_required):
        
        temp_times.append(time)
        temp_route.append(stud_route[index])
        
        if dropoff_time + sum(temp_times) > max_time:
            if len(temp_times) == 1:
                route_list.append([stud_route[index]])
                time_list.append(temp_times)
                temp_times = list()
                temp_route = list()
            else:
                time_list.append(temp_times[:-1])
                del temp_times[:-1]
                
                route_list.append(temp_route[:-1])
                del temp_route[:-1]

    time_list.append(temp_times)
    route_list.append(temp_route)
    
#    print(time_list)
#    print(route_list)

    final_list = list()
    for route in route_list:
        final_list.append(school_route + route)

    
    return final_list


test_1 = breakRoutes(current_time, school_route, stud_route, times_required)
