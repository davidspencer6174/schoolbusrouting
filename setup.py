import constants
from locations import Bus, School, Stop, Student
from utils import californiafy, timesecs

#students_file: a format I am using for special ed students
#Columns are latitude, longitude, grade level, human-readable
#description of special ed types (not used), text description.
#all_geocodes: filename for list of all geocodes. gives map from geocode to ind
#geocoded_stops: file name for map from stop to geocode
#geocoded_schools: file name for map from school to geocode
#returns a list of all students, a dict from schools to sets of
#students, and a dict from schools to indices in the travel time matrix.
#bell_sched: file name for which column 3 is cost center and
#column 4 is start time
#sped flags whether this run is for SP students or RG students.
def setup_students(students_filename, all_geocodes, geocoded_stops,
                   geocoded_schools, bell_sched, sped):
    
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
    #Maintain a dictionary of school indices to schools so that
    #school objects can be tested for equality.
    ind_school_dict = dict()
    #Maintain a set of all School objects to return                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
    all_schools = set()
    student_records = open(students_filename, 'r')
    student_records.readline()  #header
    for student_record in student_records.readlines():
        fields = student_record.split(",")
        school = fields[6].strip()
        stop_ind = codes_inds_map[fields[0].strip() + ";" + fields[1].strip()]
        school_ind = codes_inds_map[schools_codes_map[school]]
        grade = fields[2].strip()
        stud_sped = (fields[5] == "SP")
        #Not the type of student we are currently routing
        if stud_sped != sped:
            continue
        age_type = 'Other'
        try:
            grade = int(grade)
        except:
            grade = -1
        if int(grade) in constants.GRADES_TYPE_MAP:
            age_type = constants.GRADES_TYPE_MAP[int(grade)]
        if age_type == 'Other':
            print(grade)
        if school_ind not in ind_school_dict:
            belltime = 8*60*60  #default to 8AM start
            #None of the 19xxxxx schools have start times.
            if school in centers_times_map:
                belltime = centers_times_map[school]
            else:
                if constants.VERBOSE:
                    print("No time given for " + school)                    
            ind_school_dict[school_ind] = School(school_ind, belltime, fields[2])
            all_schools.add(ind_school_dict[school_ind])
        this_student = Student(stop_ind, ind_school_dict[school_ind],
                               age_type, fields, sped)
        students.append(this_student)
        schools_students_map[school].add(this_student)
        needs = fields[4].split(";")
        #Add special needs
        for need in needs:
            #Splitting an empty string returns one empty string -
            #no needs in this case
            if len(need) == 0:
                continue
            if len(need) == 1:
                #Most types of needs do not require extra info
                assert (need in ["M", "W", "L", "A", "I", "F"]), ("Unknown need type"+str(need))
                this_student.add_need(need)
            else:
                #Custom max travel time does require extra info
                #Translate from minutes to seconds
                assert (need[0] == "T"), ("Unknown need type"+str(need))
                this_student.add_need(need[0], value = int(need[1:])*60/1.5)
    student_records.close()
    return students, schools_students_map, all_schools



#bus_capacities is an input csv file where the first
#column is bus ID and the second is capacity.
def setup_buses(bus_filename, sped):
    buses = []
    bus_file = open(bus_filename, 'r')
    bus_file.readline()  #header
    for bus_info in bus_file.readlines():
        fields = bus_info.split(",")
        cap = int(fields[1])
        lift = (fields[2] == 'Y')
        #Don't include wheelchair buses when routing non-special-ed
        if not sped and lift:
            continue
        #By default, assume no wheelchair capacity.
        min_wheel = 0
        max_wheel = 0
        if len(fields) == 5 and len(fields[3]) > 0 and len(fields[4]) > 0:
            min_wheel = int(fields[3])
            max_wheel = int(fields[4])
        bus = Bus(cap, min_wheel, max_wheel, lift)
        buses.append(bus)
    bus_file.close()
    buses = sorted(buses, key = lambda x:x.capacity)
    return buses

#Sets up the stops based on the output of setup_students
#Populates unrouted_stops in the Schools
#Note: students with different cost centers may go to the same
#physical location. The loop variable "cost_cent" represents the cost
#center number, whereas student.school is the school object in memory.
#As a result, this function is the one that will associate different
#cost centers at the same location together.
def setup_stops(schools_students_map):
    stops = set()
    ttind_stop_map = dict()
    for cost_cent in schools_students_map:
        for student in schools_students_map[cost_cent]:
            dict_key = student.tt_ind
            if student.school not in ttind_stop_map:
                ttind_stop_map[student.school] = dict()
            if dict_key not in ttind_stop_map[student.school]:
                new_stop = Stop(student.school)
                ttind_stop_map[student.school][dict_key] = new_stop
                stops.add(ttind_stop_map[student.school][dict_key])
                student.school.unrouted_stops.add(new_stop)
            ttind_stop_map[student.school][dict_key].add_student(student)
    return stops
                