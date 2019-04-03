from busassignment import assign_buses
import constants
from locations import School, Stop, Student
from route import Route
from setup import setup_buses
from utils import californiafy, timesecs
import matplotlib.pyplot as plt

#Method to translate the existing routes from the phonebook to the
#Route object format
#This is kind of a mess - not intended for long-term maintenance

def existing_routes(phonebooks, all_geocodes, geocoded_stops,
                   geocoded_schools, bell_sched):
    #Generates a map from route numbers to
    #lists [route object, number of non-magnet on route]
    
    #First copied everything from setup_students to have the same info
    #Not recommended programming practice :)
    
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    belltimes = open(bell_sched, 'r')
    centers_times_map = dict()  #maps cost centers to times in seconds
    belltimes.readline()  #get rid of header
    for bell_record in belltimes.readlines():
        fields = bell_record.split(";")
        centers_times_map[fields[3]] = timesecs(fields[4])
    
    schools = open(geocoded_schools, 'r')
    schools_codes_map = dict()  #maps schools to geocodes
    schools_students_map = dict()  #maps schools to sets of students
    schools.readline()  #get rid of header
    for cost_center in schools.readlines():
         fields = cost_center.split(";")
         if len(fields) < 8:
             continue
         schools_codes_map[fields[1]] = (fields[6].strip() + ";"
                                         + fields[7].strip())
         schools_students_map[fields[1]] = set()
    schools.close()
    
    geocodes = open(all_geocodes, 'r')
    codes_inds_map = dict()
    ind = 0
    for code in geocodes.readlines():
        codes_inds_map[code.strip()] = ind
        ind += 1
    geocodes.close()
    
    schools_inds_map = dict()
    for school in schools_codes_map:
        schools_inds_map[school] = codes_inds_map[schools_codes_map[school]]
    
    students = []
    bus_col = 12
    #Maintain a dictionary of school indices to schools so that
    #school objects can be tested for equality.
    ind_school_dict = dict()
    for pb_part_filename in phonebooks:
        pb_part = open(pb_part_filename, 'r')
        pb_part.readline()  #header
        for student_record in pb_part.readlines():
            fields = student_record.split(";")
            if len(fields) <= bus_col + 6:
                continue
            if fields[bus_col + 6].strip() == ", ,":  #some buggy rows
                continue
            if fields[bus_col - 1].strip() == "9500":  #walker
                continue
            if fields[bus_col - 1].strip() == "":  #no route
                continue
            if fields[bus_col + 2].strip() not in ["1", "01"]:  #not first trip
                continue
            if fields[1].strip() == "":  #no school given
                continue
            #For now, I won't consider special ed.
            if fields[5].strip() not in ["M", "X", "P"]:
                continue
            stop = californiafy(fields[bus_col + 6])
            school = fields[1].strip()  #Cost center id
            stop_ind = codes_inds_map[stops_codes_map[stop]]
            school_ind = codes_inds_map[schools_codes_map[school]]
            grade = fields[3].strip()  #Grade level
            age_type = 'Other'
            try:
                grade = int(grade)
            except:
                grade = -1
            if int(grade) in constants.GRADES_TYPE_MAP:
                age_type = constants.GRADES_TYPE_MAP[int(grade)]
            if school_ind not in ind_school_dict:
                belltime = 8*60*60  #default to 8AM start
                #None of the 19xxxxx schools have start times.
                if school in centers_times_map:
                    belltime = centers_times_map[school]
                else:
                    if constants.VERBOSE:
                        print("No time given for " + school)                    
                ind_school_dict[school_ind] = School(school_ind, belltime)
            this_student = Student(stop_ind, ind_school_dict[school_ind],
                                   age_type, fields)
            students.append(this_student)
            schools_students_map[school].add(this_student)
        pb_part.close()

    
    
    #On to new code
    #************************************************
    
    #Map to produce
    routes_map = dict()
    
    student_records = []
    
    for pb_part_filename in phonebooks:
        pb_part = open(pb_part_filename, 'r')
        pb_part.readline()  #header
        for student_record in pb_part.readlines():
            student_records.append(student_record)
        pb_part.close()
            

    #Sort in order of pickup time
    student_records.sort(key = lambda record: timesecs(record.split(";")[16]))
            
    bus_col = 12
    
    for record in student_records:
        fields = record.split(";")
        if len(fields) <= bus_col + 6:
            continue
        if fields[bus_col + 6].strip() == ", ,":
            continue
        if fields[bus_col - 1].strip() == "9500":
            continue
        if fields[bus_col + 2].strip() not in ["1", "01"]:  #not first trip
            continue
        if fields[1].strip() == "":  #no school given
                continue
        stop = californiafy(fields[bus_col + 6])
        school = fields[1].strip()  #Cost center id
        stop_ind = codes_inds_map[stops_codes_map[stop]]
        school_ind = codes_inds_map[schools_codes_map[school]]
        grade = fields[3].strip()  #Grade level
        age_type = 'Other'
        try:
            grade = int(grade)
        except:
            grade = -1
        if int(grade) in constants.GRADES_TYPE_MAP:
            age_type = constants.GRADES_TYPE_MAP[int(grade)]
        if age_type == 'Other' and fields[5].strip() in ["M", "X", "P"]:
            print(grade)
        if school_ind not in ind_school_dict:
            belltime = 8*60*60  #default to 8AM start
            #None of the 19xxxxx schools have start times.
            if school in centers_times_map:
                belltime = centers_times_map[school]
            else:
                if constants.VERBOSE:
                    print("No time given for " + school)                    
            ind_school_dict[school_ind] = School(school_ind, belltime)
        this_student = Student(stop_ind, ind_school_dict[school_ind],
                               age_type, fields)
        route_number = int(fields[11].strip())
        if route_number not in routes_map:
            routes_map[route_number] = [Route(), 0]
        #Students the routing program routes
        if fields[5].strip() in ["M", "X", "P"]:
            route = routes_map[route_number][0]
            student_placed = False
            for stop in route.stops:
                if (stop.tt_ind == this_student.tt_ind and
                    stop.school == this_student.school and
                    stop.type == this_student.type):
                    stop.add_student(this_student)
                    student_placed = True
            if not student_placed:
                new_stop = Stop(this_student.school, this_student.type)
                new_stop.add_student(this_student)
                route.add_stop(new_stop)
        else:
            routes_map[route_number][1] += 1
            
    return routes_map

prefix = "data//"
output = existing_routes([prefix+'phonebook_parta.csv',
                         prefix+'phonebook_partb.csv'],
                         prefix+'all_geocodes.csv',
                         prefix+'stop_geocodes_fixed.csv',
                         prefix+'school_geocodes_fixed.csv',
                         prefix+'bell_times.csv')

for route_number in output:
    num_students_mxp = output[route_number][0].occupants
    num_students_notmxp = output[route_number][1]
    #print(str(num_students_mxp) + " " + str(num_students_notmxp))
    
mxp_routes = []
for route_number in output:
    num_students_mxp = output[route_number][0].occupants
    if num_students_mxp > 0:
        mxp_routes.append(output[route_number][0])
        
#cap_counts = setup_buses(prefix+'dist_bus_capacities.csv')
#mxp_routes = assign_buses(mxp_routes, cap_counts)[1]
        
occupants = sorted([route.occupants for route in mxp_routes])
lengths = sorted([route.length for route in mxp_routes])

minute_lengths = sorted([int(route.length/60) for route in mxp_routes])
shortest = minute_lengths[0]
longest = minute_lengths[-1]
#plt.hist(minute_lengths, bins = range(shortest, longest))
plt.hist(minute_lengths, bins = range(shortest//5*5, longest+5, 5))
plt.xlabel("Estimated length (minutes)")
plt.ylabel("Number of routes")
plt.title("Route length estimates - existing routes")
#plt.savefig('output//existing_routes_unbinned.eps')



#bused, = plt.plot(x, lengths_bused, 'bo', label = 'Program routes - bused')
#unbused, = plt.plot(x, lengths_unbused, 'ro', label = 'Program routes - unbused')
#existing_bused = plt.axhline(y = 691, color = 'g', label = 'Existing routes - bused')
#existing_unbused = plt.axhline(y = 451, color = 'y', label = 'Existing routes - unbused')
#plt.legend(handles = [bused, unbused, existing_bused, existing_unbused])
#plt.xlabel("Max number of minutes parameter")
#plt.ylabel("Number of routes in plan")
#plt.title("Number of routes for varying default max minutes parameter")
#plt.savefig('output//timecomparison.eps')