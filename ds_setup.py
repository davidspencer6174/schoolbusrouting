import ds_constants
from ds_locations import ds_School, ds_Stop, ds_Student
from ds_utils import californiafy, timesecs

#phonebooks: list of filenames for phonebooks
#phonebooks are assumed to be in the format that was provided to
#me in early November 2018
#all_geocodes: filename for list of all geocodes. gives map from geocode to ind
#geocoded_stops: file name for map from stop to geocode
#geocoded_schools: file name for map from school to geocode
#returns a list of all students, a dict from schools to sets of
#students, and a dict from schools to indices in the travel time matrix.
#bell_sched: file name for which column 3 is cost center and
#column 4 is start time
def setup_ds_students(phonebooks, all_geocodes, geocoded_stops,
                   geocoded_schools, bell_sched):
    
#    prefix = '/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Data/csvs/'
#    phonebooks = [prefix+'phonebook_parta.csv', prefix+'phonebook_partb.csv']
#    all_geocodes =  prefix+'all_geocodes.csv'
#    geocoded_stops = prefix+'stop_geocodes_fixed.csv'
#    geocoded_schools = prefix+'school_geocodes_fixed.csv'
#    bell_sched = prefix+'bell_times.csv'
    
    stops = open(geocoded_stops, 'r')
    stops_codes_map = dict()
    for address in stops.readlines():
        fields = address.split(";")
        if len(fields) < 3:
            continue
        stops_codes_map[fields[0]] = (fields[1].strip() + ";"
                                      + fields[2].strip())
    stops.close()
    
    belltimes = open(bell_sched, 'r', encoding='iso-8859-1')
    centers_times_map = dict()  #maps cost centers to times in seconds
    belltimes.readline()  #get rid of header
    for bell_record in belltimes.readlines():
        fields = bell_record.split(",")
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
    #Maintain a set of all School objects to return                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
    all_schools = set()
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
            if int(grade) in ds_constants.GRADES_TYPE_MAP:
                age_type = ds_constants.GRADES_TYPE_MAP[int(grade)]
            if age_type == 'Other':
                print(grade)
            if school_ind not in ind_school_dict:
                belltime = 8*60*60  #default to 8AM start
                #None of the 19xxxxx schools have start times.
                if school in centers_times_map:
                    belltime = centers_times_map[school]
                else:
                    if ds_constants.VERBOSE:
                        print("No time given for " + school)                    
                ind_school_dict[school_ind] = ds_School(school_ind, belltime, fields[2])
                all_schools.add(ind_school_dict[school_ind])
            this_student = ds_Student(stop_ind, ind_school_dict[school_ind],
                                   age_type, fields)
            students.append(this_student)
            schools_students_map[school].add(this_student)
        pb_part.close()
        
    return students, schools_students_map, all_schools



#bus_capacities is an input csv file where the first
#column is bus ID and the second is capacity.
def setup_buses(bus_capacities):
    cap_counts_dict = dict()  #map from capacities to # of buses of that capacity
    caps = open(bus_capacities, 'r', encoding='iso-8859-1')
    for bus in caps.readlines():
        fields = bus.split(",")
        cap = int(fields[1])
        if cap not in cap_counts_dict:
            cap_counts_dict[cap] = 0
        cap_counts_dict[cap] += 1
    caps.close()
    #now turn into a list sorted by capacity
    cap_counts_list = list(cap_counts_dict.items())
    cap_counts_list = sorted(cap_counts_list, key = lambda x:x[0])
    for i in range(len(cap_counts_list)):
        cap_counts_list[i] = list(cap_counts_list[i])
    return cap_counts_list

#Sets up the stops based on the output of setup_students
#Populates unds_routed_stops in the Schools
#Note: students with different cost centers may go to the same
#physical location. The loop variable "cost_cent" represents the cost
#center number, whereas student.school is the school object in memory.
#As a result, this function is the one that will associate different
#cost centers at the same location together.
def setup_ds_stops(schools_students_map):
    stops = set()
    ttind_age_stop_map = dict()
    for cost_cent in schools_students_map:
        for student in schools_students_map[cost_cent]:
            dict_key = (student.tt_ind, student.type)
            if student.school not in ttind_age_stop_map:
                ttind_age_stop_map[student.school] = dict()
            if dict_key not in ttind_age_stop_map[student.school]:
                new_stop = ds_Stop(student.school, student.type)
                ttind_age_stop_map[student.school][dict_key] = new_stop
                stops.add(ttind_age_stop_map[student.school][dict_key])
                student.school.unds_routed_stops[student.type].add(new_stop)
            ttind_age_stop_map[student.school][dict_key].add_student(student)
    return stops
                



