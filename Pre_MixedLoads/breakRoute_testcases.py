import numpy as np 

prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/School_Bus_Work/Willy_Data/mixed_load_data/"
travel_times = np.load(prefix + "travel_times.npy")

# TEST CASES
school_route = [9507]
stud_route = [7492, 8324]
max_time = 1800
current_time = 0

school_route = [10754]
stud_route = [612, 5230, 5551, 9312, 8455, 5383, 659]
max_time = 1800
current_time = 0

school_route = [10664, 10678]
stud_route = [443, 517, 535, 6782, 589, 4259, 5738]
max_time = 1000
current_time = 300


def breakRoutes(dropoff_time, school_route, stud_route):
    time_list = list()
    temp_times = list()
    base = school_route[-1]
    
    for index, stop in enumerate(stud_route):
        temp_times.append(travel_times[base][stop])

        if dropoff_time + sum(temp_times) > max_time:
            base = school_route[-1]
            if len(temp_times) == 1:
                time_list.append(temp_times)
                temp_times = list()
                
            else:
                time_list.append(temp_times[:-1])
                temp_times = list([travel_times[base][stop]])
        base = stop
        
    if temp_times:
        time_list.append(temp_times)
    
    result_list = list()
    ind = 0 
    for group in time_list:
        group_list = list()
        for stop in group:
            group_list.append(stud_route[ind])
            ind += 1
        result_list.append(school_route + group_list)

    return result_list, time_list

result_list, time_list = breakRoutes(current_time, school_route, stud_route)
print("\n")
print(result_list)
print(time_list)


