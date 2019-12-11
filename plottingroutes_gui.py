import constants
from locations import School, Student
from adjustText import adjust_text
from datetime import datetime
from diagnostics import google_maps_strings
from fuzzywuzzy import fuzz
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import tkinter
from tkinter.filedialog import askopenfilename
from tkinter.font import Font, nametofont
from utils import write_output
import webbrowser
#from graphics import GraphWin, Point, Line, Circle, Text

def geo_pixel_map(min_val, max_val, res, val):
    out = .04*res
    out += (val-min_val)/(max_val-min_val)*.92*res
    return out

#if to_plot_detailed is None, plot all routes
#Otherwise, plot schools from all routes and compute rectangle from
#all routes, but only plot the routes given in to_plot_detailed, and
#include more detailed info about them.
def plot_routes(routes, geocodes, xres, yres, to_plot_detailed = None):
    fig = plt.figure(figsize = (15, 9))
    plt.xlim(1.0 - xres, 1.0)
    plt.ylim(1.0 - yres, 1.0)
    min_y = 1000
    max_y = -1000
    min_x = 1000
    max_x = -1000
    texts = []
    for tup in routes:
        r = tup[0]
        locs = r.stops[:]
        locs.extend(r.schools)
        for loc in locs:
            x = geocodes[loc.tt_ind][1]
            y = geocodes[loc.tt_ind][0]
            min_y = min(y, min_y)
            max_y = max(y, max_y)
            min_x = min(x, min_x)
            max_x = max(x, max_x)
    schools_plotted = set()
    for tup in routes:
        r = tup[0]
        ind = tup[1]
        path = []
        for stop in r.stops:
            path.append(geocodes[stop.tt_ind])
        for school in r.schools:
            path.append(geocodes[school.tt_ind])
            if school not in schools_plotted:
                schools_plotted.add(school)
                x_pix = geo_pixel_map(min_x, max_x, xres, path[-1][1])
                y_pix = geo_pixel_map(min_y, max_y, yres, path[-1][0])
                plt.scatter([x_pix], [y_pix], s = 5, c = 'b')
                name_words = school.school_name.split()
                name_words = name_words[:-2]  #get rid of magnet name part
                to_display = ""
                for word in name_words:
                    to_display += word + " "
                to_display = to_display[:-1]
                texts.append(plt.text(x_pix, y_pix + .005, to_display,
                                      ha='center', va='center',
                                      fontsize = 12, color = 'blue'))
        points = []
        for loc in path:
            x_pix = geo_pixel_map(min_x, max_x, xres, loc[1])
            y_pix = geo_pixel_map(min_y, max_y, yres, loc[0])
            points.append((x_pix, y_pix))
        texts.append(plt.text(points[0][0], points[0][1],
                              "Route " + str(ind), ha='center', va='center',
                              fontsize = 10, color = 'red'))
        plt.plot([p[0] for p in points], [p[1] for p in points], 'k',
                 linewidth = .5)
        if to_plot_detailed != None and tup in to_plot_detailed:
            num_students = 0
            num_schools = 0
            sped_students = set()
            r = tup[0]
            for ind_inner, stop in enumerate(r.stops):
                if ind_inner > 0 and stop.tt_ind != r.stops[ind_inner - 1].tt_ind:
                    message = str(num_students) + " stud, "
                    if num_students == 1:
                        message = "1 stud, "
                    if num_schools == 1:
                        message += "1 sch"
                    else:
                        message += str(num_schools) + " sch"
                    if len(sped_students) > 0:
                        for student in sped_students:
                            message += ","
                            for need in student.needs:
                                message += need
                    texts.append(plt.text(points[ind_inner - 1][0], points[ind_inner - 1][1],
                                 message, ha='center', va='center',
                                 fontsize = 10))
                    num_students = 0
                    num_schools = 0
                    sped_students = set()
                num_schools += 1
                num_students += stop.occs
                sped_students = sped_students.union(stop.special_ed_students)
            message = str(num_students) + " stud, "
            if num_students == 1:
                message = "1 stud, "
            if num_schools == 1:
                message += "1 sch"
            else:
                message += str(num_schools) + " sch"
            if len(sped_students) > 0:
                for student in sped_students:
                    message += ","
                    for need in student.needs:
                        message += need
            texts.append(plt.text(points[len(r.stops) - 1][0],
                                  points[len(r.stops) - 1][1],
                                  message, ha='center', va='center',
                                  fontsize = 10))
    need_show_legend = False
    if to_plot_detailed != None:
        for tup in to_plot_detailed:
            for stop in tup[0].stops:
                if len(stop.special_ed_students) > 0:
                    need_show_legend = True
    if need_show_legend:
        message_legend = ("W=wheelchair\nL=non-ambulatory\nA=adult supervision\nI" +
                          "=individual supervision\nF=final stop\nT=custom time" +
                          "\nM=machine needed")
        texts.append(plt.text(.1, .1, message_legend,
                              ha='center', va='center', fontsize = 6))
    adjust_text(texts, precision = .1, text_from_points = False)
    plt.show()
    
groutes = None
geocodes = None
    
def setup_input(inputs_plotroutes):
    global prev_traveltimes_filename, routes, geocodes
    routes_file = open(inputs_plotroutes[0], "rb")
    routes = pickle.load(routes_file)
    routes_file.close()
    geocodes = []
    constants.GEOCODE_STRINGS = []
    geocodes_file = open(inputs_plotroutes[1], "r")
    for code in geocodes_file.readlines():
        constants.GEOCODE_STRINGS.append(code)
        latlong = code.split(";")
        if "\n" in latlong[1]:
            latlong[1] = latlong[1][:-2]
            latlong[0] = float(latlong[0])
            latlong[1] = float(latlong[1])
            geocodes.append(latlong)
    geocodes_file.close()
    inputs_save = open("plotting_inputs_save", "wb")
    pickle.dump(inputs_plotroutes, inputs_save)
    inputs_save.close()
    
    constants.TRAVEL_TIMES = np.load(inputs_plotroutes[2])
    try:
        constants.TRAVEL_TIMES *= float(inputs_plotroutes[3])
    except:
        constants.TRAVEL_TIMES *= 1.5
    
    
def plot_routes_gui():
    global inputs_plotroutes, textboxes_plotroutes, school_textboxes_plotroutes
    global routes, geocodes, name_format_var
    
    if routes == None:
        routes, geocodes = setup_input(inputs_plotroutes)
        
    inputs_save = open("plotting_inputs_save", "wb")
    pickle.dump(inputs_plotroutes, inputs_save)
    inputs_save.close()
    
    routes_to_plot = []
    plotting_type = name_format_var.get()
    print(plotting_type)
    to_plot_string = school_textboxes_plotroutes[plotting_type - 1].get("1.0", tkinter.END)
    to_plot_strings = to_plot_string.split(",")
    for i in range(len(to_plot_strings)):
        to_plot_strings[i] = to_plot_strings[i].strip().upper()
        if plotting_type == 1 or plotting_type == 4:
            to_plot_strings[i] = int(to_plot_strings[i])
            
    #Handle fuzzy string matching - replace with exact strings
    if plotting_type == 3:
        all_schools = set()
        for route in routes:
            for school in route.schools:
                all_schools.add(school)
        exact_to_plot_strings = []
        for to_plot_string in to_plot_strings:
            best_fuzzy_score = 0
            best_name = ""
            to_plot_string = to_plot_string.strip().upper()
            for school in all_schools:
                match_school_string = school.school_name.strip().upper()
                this_score = (fuzz.ratio(to_plot_string, match_school_string) +
                              fuzz.partial_ratio(to_plot_string, match_school_string) +
                              fuzz.token_sort_ratio(to_plot_string, match_school_string))
                if this_score > best_fuzzy_score:
                    best_fuzzy_score = this_score
                    best_name = school.school_name
            print("School name to match: " + to_plot_string)
            print("Closest match: " + best_name)
            exact_to_plot_strings.append(best_name)
        plotting_type = 2
        to_plot_strings = exact_to_plot_strings
    print(to_plot_strings)
        
    for route_ind in range(len(routes)):
        route = routes[route_ind]
        to_add = False
        #Determine whether the route should be included
        if plotting_type == 1:
            for stop in route.stops:
                for student in stop.students:
                    if int(student.fields[6]) in to_plot_strings:
                        to_add = True
        if plotting_type == 2:
            for school in route.schools:
                if school.school_name in to_plot_strings:
                    to_add = True
        if plotting_type == 4:
            if route_ind in to_plot_strings:
                to_add = True
        if to_add:
            routes_to_plot.append([route, route_ind])
    if plotting_type == 4:
        plot_routes(routes_to_plot, geocodes, 1.0, 0.98, to_plot_detailed = routes_to_plot)
    else:
        plot_routes(routes_to_plot, geocodes, 1.0, 0.98)
        
def open_gmaps():
    global school_textboxes_plotroutes, routes
    
    route_to_open_string = school_textboxes_plotroutes[4].get("1.0", tkinter.END).strip()
    route_to_open = int(route_to_open_string)
    urls_to_open = google_maps_strings(routes[route_to_open])
    for url in urls_to_open:
        webbrowser.open_new(url)
  
working_route1 = None
working_route2 = None
route1_num = 0
route2_num = 0
listbox1 = None
listbox2 = None
r1_edit = None
r2_edit = None

def promote_selected():
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit
    selected_1 = listbox1.curselection()
    selected_2 = listbox2.curselection()
    new_selected_1 = []
    new_selected_2 = []
    for sel in selected_1:
        if sel > 0 and sel < len(r1_edit.stops):
            r1_edit.stops[sel - 1:sel + 1] = r1_edit.stops[sel - 1:sel + 1][::-1]
            new_selected_1.append(sel - 1)
        elif sel > len(r1_edit.stops):
            ind = sel - len(r1_edit.stops)
            r1_edit.schools[ind - 1:ind + 1] = r1_edit.stops[ind - 1:ind + 1][::-1]
            new_selected_1.append(sel - 1)
        else:
            new_selected_1.append(sel)
    for sel in selected_2:
        if sel > 0 and sel < len(r2_edit.stops):
            r2_edit.stops[sel - 1:sel + 1] = r2_edit.stops[sel - 1:sel + 1][::-1]
            new_selected_2.append(sel - 1)
        elif sel > len(r2_edit.stops):
            ind = sel - len(r2_edit.stops)
            r2_edit.schools[ind - 1:ind + 1] = r2_edit.stops[ind - 1:ind + 1][::-1]
            new_selected_2.append(sel - 1)
        else:
            new_selected_2.append(sel)
    listboxes_populate()
    listbox1.selection_clear(0)
    listbox2.selection_clear(0)
    for sel in new_selected_1:
        listbox1.select_set(sel, sel)
    for sel in new_selected_2:
        listbox2.select_set(sel, sel)
        
def demote_selected():
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit
    selected_1 = list(listbox1.curselection())
    selected_1.sort()
    selected_2 = list(listbox2.curselection())
    selected_2.sort()
    new_selected_1 = []
    new_selected_2 = []
    for sel in selected_1:
        if sel < len(r1_edit.stops) - 1:
            r1_edit.stops[sel:sel + 2] = r1_edit.stops[sel:sel + 2][::-1]
            new_selected_1.append(sel + 1)
        elif sel >= len(r1_edit.stops) and sel < len(r1_edit.stops) + len(r1_edit.schools) - 1:
            ind = sel - len(r1_edit.stops)
            r1_edit.schools[ind:ind + 2] = r1_edit.stops[ind:ind + 2][::-1]
            new_selected_1.append(sel + 1)
        else:
            new_selected_1.append(sel)
    for sel in selected_2:
        if sel < len(r2_edit.stops) - 1:
            r2_edit.stops[sel:sel + 2] = r2_edit.stops[sel:sel + 2][::-1]
            new_selected_2.append(sel + 1)
        elif sel >= len(r2_edit.stops) and sel < len(r2_edit.stops) + len(r2_edit.schools) - 1:
            ind = sel - len(r2_edit.stops)
            r2_edit.schools[ind:ind + 2] = r2_edit.stops[ind:ind + 2][::-1]
            new_selected_2.append(sel + 1)
        else:
            new_selected_2.append(sel)
    listboxes_populate()
    listbox1.selection_clear(0)
    listbox2.selection_clear(0)
    for sel in new_selected_1:
        listbox1.select_set(sel, sel)
    for sel in new_selected_2:
        listbox2.select_set(sel, sel)
        
def left_to_right():
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit
    selected = list(listbox1.curselection())
    selected.sort()
    selected = selected[::-1]
    to_move = []
    for sel in selected:
        if sel < len(r1_edit.stops):
            to_move.append(r1_edit.stops[sel])
            r1_edit.remove_stop(r1_edit.stops[sel])
    for moving in to_move:
        r2_edit.add_stop(moving)
    listboxes_populate()
    listbox1.selection_clear(0)
    listbox2.selection_clear(0)
    listbox2.select_set(len(r2_edit.stops) - len(to_move), len(r2_edit.stops) - 1)
    
    
def right_to_left():
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit
    selected = list(listbox2.curselection())
    selected.sort()
    selected = selected[::-1]
    to_move = []
    for sel in selected:
        if sel < len(r2_edit.stops):
            to_move.append(r2_edit.stops[sel])
            r2_edit.remove_stop(r2_edit.stops[sel])
    for moving in to_move:
        r1_edit.add_stop(moving)
    listboxes_populate()
    listbox1.selection_clear(0)
    listbox2.selection_clear(0)
    listbox1.select_set(len(r1_edit.stops) - len(to_move), len(r1_edit.stops) - 1)

    
def revert_changes():
    global routes
    
    if routes == None:
        routes, geocodes = setup_input(inputs_plotroutes)
        
    for r in routes:
        try:
            r.restore("before_edits")
        except:
            continue

def save_changes():
    global routes, geocodes
    
    if routes == None:
        routes, geocodes = setup_input(inputs_plotroutes)
        
    output_filename = datetime.now().strftime("output//results_%Y-%m-%d_%H%M%S.csv")
    write_output(None, output_filename, routes)
    
    object_output_filename = datetime.now().strftime("output//obj_files_%Y-%m-%d_%H%M%S.obj")
    saving_objects = open(object_output_filename, "wb")
    pickle.dump(routes, saving_objects)
    saving_objects.close()

            
def listboxes_populate():
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit
    listbox1.delete(0, tkinter.END)
    listbox2.delete(0, tkinter.END)
    
    displaystrings_1 = []
    displaystrings_2 = []
    for stop in r1_edit.stops:
        displaystrings_1.append("Stop with " + str(stop.occs) +
                                " students for " + stop.school.school_name)
    for school in r1_edit.schools:
        displaystrings_1.append(school.school_name)
    for stop in r2_edit.stops:
        displaystrings_2.append("Stop with " + str(stop.occs) +
                                " students for " + stop.school.school_name)
    for school in r2_edit.schools:
        displaystrings_2.append(school.school_name)
    
            
    for to_show in displaystrings_1:
        listbox1.insert(tkinter.END, to_show)
    for to_show in displaystrings_2:
        listbox2.insert(tkinter.END, to_show)
    
    
def edit_routes():
    global school_textboxes_plotroutes, inputs_plotroutes
    global working_route1, working_route2, route1_num, route2_num
    global listbox1, listbox2, r1_edit, r2_edit, routes, geocodes
    
    if routes == None:
        routes, geocodes = setup_input(inputs_plotroutes)
    
    route1_num = int(school_textboxes_plotroutes[5].get("1.0", tkinter.END).strip())
    route2_num = int(school_textboxes_plotroutes[6].get("1.0", tkinter.END).strip())
    r1_edit = routes[route1_num]
    r2_edit = routes[route2_num]
    r1_edit.backup("before_edits")
    r2_edit.backup("before_edits")
    
    root_editroutes = tkinter.Tk()
    
    r1label = tkinter.Label(root_editroutes, text = str(route1_num))
    r1label.grid(row = 0, column = 0)
    r2label = tkinter.Label(root_editroutes, text = str(route2_num))
    r2label.grid(row = 0, column = 1)
    
    listbox1 = tkinter.Listbox(root_editroutes, selectmode = tkinter.EXTENDED,
                               width = 50)
    listbox1.grid(row = 1, column = 0)
    listbox2 = tkinter.Listbox(root_editroutes, selectmode = tkinter.EXTENDED,
                               width = 50)
    listbox2.grid(row = 1, column = 1)
    
    listboxes_populate()
    
    promote_button = tkinter.Button(root_editroutes,
                                    text = "Move all selections earlier",
                                    command = promote_selected)
    promote_button.grid(row = 2, column = 0)
    
    demote_button = tkinter.Button(root_editroutes,
                                    text = "Move all selections later",
                                    command = demote_selected)
    demote_button.grid(row = 2, column = 1)
    
    left_to_right_button = tkinter.Button(root_editroutes,
                                          text = "Move selections from " + str(route1_num) + " to " + str(route2_num),
                                          command = left_to_right)
    left_to_right_button.grid(row = 3, column = 0)
    
    right_to_left_button = tkinter.Button(root_editroutes,
                                          text = "Move selections from " + str(route2_num) + " to " + str(route1_num),
                                          command = right_to_left)
    right_to_left_button.grid(row = 3, column = 1)
    
    
    return False

   
def set_file_text(index, text):
    global textboxes_plotroutes, inputs_plotroutes
    textboxes_plotroutes[index].delete(1.0, tkinter.END)
    textboxes_plotroutes[index].insert(tkinter.END, text)
    setup_input(inputs_plotroutes)

def set_file(index):
    global inputs_plotroutes
    inputs_plotroutes[index] = askopenfilename()
    set_file_text(index, inputs_plotroutes[index])
    
def run_gui_plotroutes():
    global time_elapsed_label, inputs_plotroutes, buttons_plotroutes, textboxes_plotroutes, name_format_var, school_textboxes_plotroutes
    
    files_needed_plotroutes = ["Route plan object file", "Geocodes for map data",
                               "Map data", "Travel time matrix multiplier (default 1.5)"]    
    
    inputs_plotroutes = None
    try:
        inputs_save = open("plotting_inputs_save", "rb")
        inputs_plotroutes = pickle.load(inputs_save)
        inputs_save.close()
    except:
        inputs_plotroutes = ["" for i in range(4)]
    
    root_plotroutes = tkinter.Tk()
    textboxes_plotroutes = [None for i in range(4)]
    buttons_plotroutes = [None for i in range(4)]
    school_textboxes_plotroutes = [None for i in range(7)]

    default_font_plotroutes = nametofont("TkDefaultFont")
    fontsize_plotroutes = 11
    default_font_plotroutes.configure(size=fontsize_plotroutes)
    
    for i in range(4):
        this_frame = tkinter.Frame(root_plotroutes)
        this_frame.pack(side = tkinter.TOP)
        
        buttons_plotroutes[i] = tkinter.Button(root_plotroutes, text=files_needed_plotroutes[i], command = lambda c=i: set_file(c))
        if i == 3:
            buttons_plotroutes[i] = tkinter.Label(root_plotroutes, text=files_needed_plotroutes[i])
        textboxes_plotroutes[i] = tkinter.Text(root_plotroutes, height = 1)
        
        set_file_text(i, inputs_plotroutes[i])
        buttons_plotroutes[i].pack(in_ = this_frame, side = tkinter.LEFT)
        textboxes_plotroutes[i].pack()
        
    name_format_var = tkinter.IntVar(root_plotroutes)
        
    cost_cent_frame = tkinter.Frame(root_plotroutes)
    cost_cent_rbutton = tkinter.Radiobutton(root_plotroutes, text = "Plot school(s) with cost center number(s)", variable = name_format_var, value = 1)
    cost_cent_rbutton.pack(in_ = cost_cent_frame, side = tkinter.LEFT)
    cost_cent_rbutton.select()
    school_textboxes_plotroutes[0] = tkinter.Text(root_plotroutes, height = 1, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[0].pack(in_ = cost_cent_frame, side = tkinter.LEFT)
    cost_cent_frame.pack()

    exact_frame = tkinter.Frame(root_plotroutes)
    tkinter.Radiobutton(root_plotroutes, text = "Plot school(s) with exact name(s)", variable = name_format_var, value = 2).pack(in_ = exact_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[1] = tkinter.Text(root_plotroutes, height = 1, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[1].pack(in_ = exact_frame, side = tkinter.LEFT)    
    exact_frame.pack()
    
    approx_frame = tkinter.Frame(root_plotroutes)
    tkinter.Radiobutton(root_plotroutes, text = "Plot school(s) with approximate name(s)", variable = name_format_var, value = 3).pack(in_ = approx_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[2] = tkinter.Text(root_plotroutes, height = 1, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[2].pack(in_ = approx_frame, side = tkinter.LEFT)
    approx_frame.pack()
    
    bynumber_frame = tkinter.Frame(root_plotroutes)
    tkinter.Radiobutton(root_plotroutes, text = "Plot route(s) by route number(s)", variable = name_format_var, value = 4).pack(in_ = bynumber_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[3] = tkinter.Text(root_plotroutes, height = 1, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[3].pack(in_ = bynumber_frame, side = tkinter.LEFT)
    bynumber_frame.pack()
    
    start_button = tkinter.Button(root_plotroutes, text="Plot Routes", command = plot_routes_gui)
    start_button.pack()
    
    gmapsroute_frame = tkinter.Frame(root_plotroutes)
    tkinter.Button(root_plotroutes, text="View route in Google Maps by route number", command = open_gmaps).pack(in_ = gmapsroute_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[4] = tkinter.Text(root_plotroutes, height = 1, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[4].pack(in_ = gmapsroute_frame, side = tkinter.LEFT)
    gmapsroute_frame.pack()
    
    editing_frame = tkinter.Frame(root_plotroutes)
    tkinter.Button(root_plotroutes, text="Edit pair of routes by route number", command = edit_routes).pack(in_ = editing_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[5] = tkinter.Text(root_plotroutes, height = 1, width = 30, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[6] = tkinter.Text(root_plotroutes, height = 1, width = 30, font = ("Courier", fontsize_plotroutes))
    school_textboxes_plotroutes[5].pack(in_ = editing_frame, side = tkinter.LEFT)
    school_textboxes_plotroutes[6].pack(in_ = editing_frame, side = tkinter.LEFT)
    editing_frame.pack()
    
    editing_management_frame = tkinter.Frame(root_plotroutes)
    revert_button = tkinter.Button(root_plotroutes,
                                   text = "Restore Original Routes",
                                   command = revert_changes)
    revert_button.pack(in_ = editing_management_frame, side = tkinter.LEFT)
    
    save_button = tkinter.Button(root_plotroutes,
                                 text = "Save Changes (will create new files)",
                                 command = save_changes)
    save_button.pack(in_ = editing_management_frame, side = tkinter.LEFT)
    editing_management_frame.pack()
    
    root_plotroutes.mainloop()