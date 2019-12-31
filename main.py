import constants
import copy
from datetime import datetime
from greedymoves import make_greedy_moves
from time import process_time
from locations import Student
from mixedloads import mixed_loads
import pickle
import random
from setup import setup_buses, setup_map_data, setup_stops, setup_students, setup_mod_caps, setup_parameters, setup_school_pairs
from generateroutes import generate_routes
from busassignment_bruteforce import assign_buses
from plottingroutes_gui import run_gui_plotroutes
import numpy as np
import threading
import tkinter
from tkinter.filedialog import askopenfilename
from tkinter.font import Font, nametofont
from utils import improvement_procedures, stud_trav_time_array, mstt, write_output

#For questions, contact davidspencer6174@gmail.com

global start_time
global start_time_orig
run_finished = False

def main(method, sped, partial_route_plan = None, permutation = None,
         improve = False, to_bus = False):
    global routing_type_var, school_textboxes
    routing_type = routing_type_var.get()
    school_string = ""
    if routing_type > 1:
        school_string = school_textboxes[routing_type - 2].get("1.0", tkinter.END)
    output = setup_students(constants.FILENAMES[0],
                            constants.FILENAMES[4],
                            constants.FILENAMES[1],
                            sped,
                            routing_type,
                            school_string.split(","))
    students = output[0]
    schools_students_map = output[1]
    all_schools = output[2]
    stops = setup_stops(schools_students_map)
    setup_school_pairs(constants.FILENAMES[8], constants.FILENAMES[7])
    buses = setup_buses(constants.FILENAMES[2], sped)
    setup_mod_caps(constants.FILENAMES[5])
    if constants.VERBOSE:
        print(len(students))
        schools_count = set()
        for student in students:
            schools_count.add(student.school)
        print(len(schools_count))
        print(len(schools_students_map))
        
    routes = None
    
    if method == "mine":
        routes = generate_routes(all_schools, permutation = permutation,
                             partial_route_plan = partial_route_plan, sped = sped)
        
    if len(routes) == 0:
        return routes

    for route in routes:
        assert route.feasibility_check(verbose = True)
    
    if improve:
        improvement_procedures(routes, [not sped, True, True])
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
        
    #As per dicussions in early July 2019, we decided
    #not to have the program attempt bus assignment
    #for special ed.
    if to_bus and not sped:
        routes = assign_buses(routes, buses)
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
        
    if improve:
        improvement_procedures(routes, [not sped, True, True])
        
    for route in routes:
        assert route.feasibility_check(verbose = True)
    
    if constants.VERBOSE:
        print("Number of routes: " + str(len(routes)))
    
    all_verified = True
    for route in routes:
        if not route.feasibility_check(verbose = True):
            all_verified = False
    if constants.VERBOSE:
        print("All routes verified.")
    
    return routes
    
routes_returned = None

def permutation_approach(sped, iterations = 100, minutes = None):
    global start_time
    #Uncomment latter lines to use an existing permutation
    best_perm = None
    best_routes = None
    #loading_perm = open(("output//lastperm55m.obj"), "rb")
    #loading_perm = open(("output//newagerestrictionperm.obj"), "rb")
    #best_perm = pickle.load(loading_perm)
    #loading_perm.close()
    best_num_routes = 100000
    best_mstt = 100000
    score_function = lambda num_routes, plan_mstt: num_routes + constants.MSTT_WEIGHT*plan_mstt
    #score_function = lambda num_routes, plan_mstt: num_routes + 6*plan_mstt/500
    best_score = score_function(best_num_routes, best_mstt)
    
    best_mstt_per_num_routes = dict()
    
    successes = []
    new_perm = None
    for test in range(iterations):
        if test > 0:
            #Try a few swaps
            new_perm = copy.copy(best_perm)
            num_to_swap = random.randint(1, 40)
            for swap in range(num_to_swap):
                #Bias toward early stops, since these are more important
                ind1 = random.randint(0, min(40, len(new_perm) - 1))
                if random.random() < .9:
                    ind1 = random.randint(0, len(new_perm) - 1)
                ind2 = random.randint(0, len(new_perm) - 1)
                new_perm[ind1], new_perm[ind2] = new_perm[ind2], new_perm[ind1]
        #Test the route
        new_routes_returned = main("mine", sped, permutation = new_perm, improve = True, to_bus = True)
        if len(new_routes_returned) == 0:
            return []
        if best_perm == None:
            all_stops = set()
            for route in new_routes_returned:
                for stop in route.stops:
                    all_stops.add(stop)
            new_perm = list(range(len(all_stops)))
            best_perm = list(range(len(all_stops)))
        new_num_routes = len(new_routes_returned)
        new_mstt = mstt(new_routes_returned)/60
        #new_score = new_num_routes + 6*new_mstt/500
        new_score = score_function(new_num_routes, new_mstt)
        if new_num_routes not in best_mstt_per_num_routes:
            best_mstt_per_num_routes[new_num_routes] = (new_mstt, new_routes_returned)
        if new_mstt < best_mstt_per_num_routes[new_num_routes][0]:
            best_mstt_per_num_routes[new_num_routes] = (new_mstt, new_routes_returned)
            print("Made an improvement")
            for num_r in best_mstt_per_num_routes:
                print((num_r, best_mstt_per_num_routes[num_r][0]))
        if (new_score < best_score):
            print("New best")
            print(new_score)
            best_perm = new_perm
            best_mstt = new_mstt
            best_num_routes = new_num_routes
            best_score = new_score
            best_routes = new_routes_returned
            if test > 0:
                successes.append(num_to_swap)
        if minutes != None:
            #Check whether we have already exceeded the maximum time
            if process_time() - start_time > 60*minutes:
                break
            #Check whether the next iteration is likely to
            #exceed the maximum time
            if (process_time() - start_time)*(test+2)/(test+1) > 60*minutes:
                break
        print(str(new_num_routes) + " " + str(new_mstt))
    return best_routes


#Larger mstt_weights will prioritize travel time over
#the number of routes.
def vary_params(sped, minutes = None):
    global start_time
    best_score = 100000000
    best_params = ()
    best_results = []
    for i in range(1000):
        #Set up parameters with some randomness
        constants.SCH_DIST_WEIGHT = random.random()*.5 + .7
        constants.STOP_DIST_WEIGHT = random.random()*.2
        constants.EVALUATION_CUTOFF = random.random()*500 - 300
        
        #Test these parameters
        routes_returned = main("mine", sped)
        
        #Take measurements of the result
        num_routes = len(routes_returned)
        if num_routes == 0: #No students
            return []
        stud_trav_times = stud_trav_time_array(routes_returned)
        mean_stud_trav_time = np.mean(stud_trav_times)/60
        
        
        
        #Set up the result to store. If it is dominated by
        #another result, we won't store it; if it dominates
        #another result, we will delete that one.
        result = (num_routes, mean_stud_trav_time,
                  constants.SCH_DIST_WEIGHT,
                  constants.STOP_DIST_WEIGHT, constants.EVALUATION_CUTOFF,
                  constants.MAX_SCHOOL_DIST)
        if num_routes + constants.MSTT_WEIGHT*mean_stud_trav_time < best_score:
            best_score = num_routes + constants.MSTT_WEIGHT*mean_stud_trav_time
            best_params = (constants.SCH_DIST_WEIGHT, constants.STOP_DIST_WEIGHT,
                           constants.EVALUATION_CUTOFF, constants.MAX_SCHOOL_DIST)
        strictly_worse = False
        to_remove = set()
        for other_result in best_results:
            if other_result[0] <= result[0] and other_result[1] <= result[1]:
                strictly_worse = True
                break
            if result[0] <= other_result[0] and result[1] <= other_result[1]:
                to_remove.add(other_result)
        if not strictly_worse:
            best_results.append(result)
            for worse_one in to_remove:
                best_results.remove(worse_one)
            print(sorted([i[:2] for i in best_results], key=lambda x:x[0]))
        print(str(constants.SCH_DIST_WEIGHT) + " " +
              str(constants.STOP_DIST_WEIGHT) + " " +
              str(constants.EVALUATION_CUTOFF) + " " +
              str(constants.MAX_SCHOOL_DIST) + " " +
              str(len(routes_returned)) + " " + 
              str(mean_stud_trav_time))
        if minutes != None:
            #Check whether we have already exceeded the maximum time
            if process_time() - start_time > 60*minutes:
                break
            #Check whether the next iteration is likely to
            #exceed the maximum time
            if (process_time() - start_time)*(i+2)/(i+1) > 60*minutes:
                break
    (constants.SCH_DIST_WEIGHT, constants.STOP_DIST_WEIGHT,
     constants.EVALUATION_CUTOFF, constants.MAX_SCHOOL_DIST) = best_params
    return best_results

working_on_sped = True

#Does a full run, that is, makes a route plan for special ed
#without considering buses and makes a route plan for
#magnet with consideration of buses.
def full_run():
    global start_time, start_time_orig, working_on_sped, run_finished
    run_finished = False
    setup_map_data(constants.FILENAMES[3])
    #First, try to find good parameters by doing quick runs that
    #don't do improvement procedures or bus assignment.
    setup_parameters(constants.FILENAMES[6], True)
    working_on_sped = True
    start_time = process_time()
    start_time_orig = process_time()
    print("Searching for good algorithm parameters for special ed.")
    vary_params(True, minutes = min(20, constants.MINUTES_PER_SEGMENT/2))
    print("Special ed parameters chosen. Beginning routing")
    start_time = process_time()
    sped_routes = permutation_approach(True, minutes = constants.MINUTES_PER_SEGMENT*3/2)
    print("Special ed routing finished.")
    setup_parameters(constants.FILENAMES[6], False)
    working_on_sped = False
    start_time = process_time()
    start_time_orig = process_time()
    print("Searching for good algorithm parameters for magnet routing.")
    vary_params(False, minutes = min(20, constants.MINUTES_PER_SEGMENT/2))
    print("Magnet parameters chosen. Beginning routing")
    start_time = process_time()
    magnet_routes = permutation_approach(False, minutes = constants.MINUTES_PER_SEGMENT*3/2)
    print("Magnet routing finished.")
    all_routes = sped_routes + magnet_routes
    print("Final number of magnet routes: " + str(len(magnet_routes)))
    print("Mean student travel time of magnet routes: " + str(mstt(magnet_routes)) + " minutes")
    print("Final number of special ed routes: " + str(len(sped_routes)))
    print("Mean student travel time of special ed routes: " + str(mstt(sped_routes)) + " minutes")
    
    output_filename = datetime.now().strftime("output//results_%Y-%m-%d_%H%M%S.csv")
    write_output(constants.FILENAMES[0], output_filename, all_routes)
    
    object_output_filename = datetime.now().strftime("output//obj_files_%Y-%m-%d_%H%M%S.obj")
    saving_objects = open(object_output_filename, "wb")
    pickle.dump(all_routes, saving_objects)
    saving_objects.close()
    run_finished = True
    return all_routes

files_needed = ["Student data", "School data", "Bus data", "Map data",
                "Geocodes for map data", "Bus capacities for different ages",
                "Parameters", "Explicitly allowed school pairs (optional)",
                "Explicitly forbidden school pairs (optional)"]

root = tkinter.Tk()
root.title("Bus Route Generation")
textboxes = [None for i in range(9)]
buttons = [None for i in range(9)]
school_textboxes = [None for i in range(3)]
time_elapsed_label = None

default_font = nametofont("TkDefaultFont")
fontsize = 11
default_font.configure(size=fontsize)

filenames = None
try:
    filenames_save = open("filenames_save", "rb")
    filenames = pickle.load(filenames_save)
    filenames_save.close()
    print(filenames)
except:
    filenames = ["" for i in range(9)]
    
#Determines whether to route for a single school or all schools
routing_type_var = tkinter.IntVar(root)
        

def update_time():
    minutes_elapsed = int((process_time() - start_time_orig)/60)
    to_display_text = "Initializing"
    if constants.MINUTES_PER_SEGMENT != None:
        to_display_text = "Working on non-special ed routes\n"
        if working_on_sped:
            to_display_text = "Working on special ed routes\n"
        to_display_text += (str(minutes_elapsed) + " minutes out of " +
                            "approximately " + str(int(constants.MINUTES_PER_SEGMENT*2)) +
                            " minutes.")
    
    time_elapsed_label.config(text = to_display_text)
    if run_finished:
        time_elapsed_label.config(text = "Done")
        return
    root.after(10000, lambda: update_time())

def set_file_text(index, text):
    textboxes[index].delete(1.0, tkinter.END)
    textboxes[index].insert(tkinter.END, text)

def set_file(index):
    filenames[index] = askopenfilename()
    set_file_text(index, filenames[index])
  
def create_routes():
    global start_time, start_time_orig
    constants.FILENAMES = filenames
    constants.GEOCODE_CACHE = dict()
    
    #Save filenames to prevent having to type them in every time
    filenames_save = open("filenames_save", "wb")
    pickle.dump(filenames, filenames_save)
    filenames_save.close()
    
    threading.Thread(target = full_run).start()
    start_time = process_time()
    start_time_orig = process_time()
    update_time()
    
def open_spec(i):
    spec_root = tkinter.Tk()
    mess = tkinter.Message(spec_root, text = constants.SPEC_TEXT[i], font = ("Helvetica", fontsize))
    mess.pack()    
    spec_root.mainloop()

def run_gui(buttons, textboxes):
    global time_elapsed_label, filenames
     
    for i in range(9):
        this_frame = tkinter.Frame(root)
        this_frame.pack(side = tkinter.TOP)
        
        buttons[i] = tkinter.Button(root, text=files_needed[i], command = lambda c=i: set_file(c))
        spec_button = tkinter.Button(root, text="View Specification", command = lambda c=i: open_spec(c))
        textboxes[i] = tkinter.Text(root, height = 1, font = ("Courier", fontsize))
        
        set_file_text(i, filenames[i])
        buttons[i].pack(in_ = this_frame, side = tkinter.LEFT)
        spec_button.pack(in_ = this_frame, side = tkinter.LEFT)
        textboxes[i].pack()

    all_schools_rbutton = tkinter.Radiobutton(root, text = "Route all schools", variable = routing_type_var, value = 1)
    all_schools_rbutton.pack()
    all_schools_rbutton.select()
    
    cost_cent_frame = tkinter.Frame(root)
    tkinter.Radiobutton(root, text = "Route school(s) with cost center number(s)", variable = routing_type_var, value = 2).pack(in_ = cost_cent_frame, side = tkinter.LEFT)
    school_textboxes[0] = tkinter.Text(root, height = 1, font = ("Courier", fontsize))
    school_textboxes[0].pack(in_ = cost_cent_frame, side = tkinter.LEFT)
    cost_cent_frame.pack()

    exact_frame = tkinter.Frame(root)
    tkinter.Radiobutton(root, text = "Route school(s) with exact name(s)", variable = routing_type_var, value = 3).pack(in_ = exact_frame, side = tkinter.LEFT)
    school_textboxes[1] = tkinter.Text(root, height = 1, font = ("Courier", fontsize))
    school_textboxes[1].pack(in_ = exact_frame, side = tkinter.LEFT)    
    exact_frame.pack()
    
    approx_frame = tkinter.Frame(root)
    tkinter.Radiobutton(root, text = "Route school(s) with approximate name(s)", variable = routing_type_var, value = 4).pack(in_ = approx_frame, side = tkinter.LEFT)
    school_textboxes[2] = tkinter.Text(root, height = 1, font = ("Courier", fontsize))
    school_textboxes[2].pack(in_ = approx_frame, side = tkinter.LEFT)
    approx_frame.pack()

     
    start_button = tkinter.Button(root, text="Create Routes", command = create_routes)
    start_button.pack()
    
    plotting_button = tkinter.Button(root, text="Open Route Viewing/Editing Utility", command = run_gui_plotroutes)
    plotting_button.pack()
    
    time_elapsed_label = tkinter.Label(root, text = '')
    time_elapsed_label.pack()
    
    root.mainloop()
    
run_gui(buttons, textboxes)