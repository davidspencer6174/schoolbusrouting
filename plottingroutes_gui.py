import constants
from locations import School, Student
from adjustText import adjust_text
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import tkinter
from tkinter.filedialog import askopenfilename
from tkinter.font import Font, nametofont
#from graphics import GraphWin, Point, Line, Circle, Text

def geo_pixel_map(min_val, max_val, res, val):
    out = .04*res
    out += (val-min_val)/(max_val-min_val)*.92*res
    return out

#if to_plot is None, plot all routes
#Otherwise, plot schools from all routes and compute rectangle from
#all routes, but only plot the routes given in to_plot.
#If to_plot is not None, filename also should not be None.
def plot_routes(routes, geocodes, xres, yres, to_plot = None, filename = None):
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
                #sch_circ = mpatches.Circle(sch_point, 5,
                #                           color = "blue", fill = True,
                #                           transform = fig.transFigure)
                #fig.patches.append(sch_circ)
                print(school.school_name)
                name_words = school.school_name.split()
                name_words = name_words[:-2]  #get rid of magnet name part
                print(name_words)
                to_display = ""
                for word in name_words:
                    to_display += word + " "
                to_display = to_display[:-1]
                print(to_display)
                texts.append(plt.text(x_pix, y_pix + .005, to_display,
                                      ha='center', va='center',
                                      fontsize = 12, color = 'blue'))
        if to_plot != None and r not in to_plot:
            continue
        points = []
        for loc in path:
            #print([min_x, max_x, xres, loc[0]])
            #print([min_y, max_y, yres, loc[1]])
            x_pix = geo_pixel_map(min_x, max_x, xres, loc[1])
            y_pix = geo_pixel_map(min_y, max_y, yres, loc[0])
            #print(x_pix)
            #print(y_pix)
            points.append((x_pix, y_pix))
        texts.append(plt.text(points[0][0], points[0][1],
                              "Route " + str(ind), ha='center', va='center',
                              fontsize = 10, color = 'red'))
        plt.plot([p[0] for p in points], [p[1] for p in points], 'k',
                 linewidth = .5)
        print(points)
        if to_plot != None:
            num_students = 0
            num_schools = 0
            sped_students = set()
            for ind, stop in enumerate(r.stops):
                if ind > 0 and stop.tt_ind != r.stops[ind - 1].tt_ind:
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
                    texts.append(plt.text(points[ind - 1][0], points[ind - 1][1],
                                          message, ha='center', va='center',
                                          fontsize = 20))
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
                                         fontsize = 20))
    need_show_legend = False
    if to_plot != None:
        for r in to_plot:
            if len(r.special_ed_students) > 0:
                need_show_legend = True
    if need_show_legend:
        message_legend = ("W=wheelchair\nL=non-ambulatory\nA=adult supervision\nI" +
                          "=individual supervision\nF=final stop\nT=custom time" +
                          "\nM=machine needed")
        texts.append(plt.text(.1, .1, message_legend,
                              ha='center', va='center', fontsize = 6))
    adjust_text(texts, precision = .1, text_from_points = False)
    plt.show()
    
    
def plot_routes_gui():
    global inputs, textboxes
    routes_file = open(inputs[0], "rb")
    routes = pickle.load(routes_file)
    routes_file.close()
    geocodes = []
    geocodes_file = open(inputs[1], "r")
    for code in geocodes_file.readlines():
        latlong = code.split(";")
        if "\n" in latlong[1]:
            latlong[1] = latlong[1][:-2]
            latlong[0] = float(latlong[0])
            latlong[1] = float(latlong[1])
            geocodes.append(latlong)
    geocodes_file.close()
    routes_to_plot = []
    inputs[2] = textboxes[2].get("1.0", tkinter.END)
    inputs_save = open("plotting_inputs_save", "wb")
    pickle.dump(inputs, inputs_save)
    inputs_save.close()
    cost_centers = inputs[2].split(",")
    for i in range(len(cost_centers)):
        cost_centers[i] = cost_centers[i].strip()
    for route_ind in range(len(routes)):
        route = routes[route_ind]
        to_add = False
        for stop in route.stops:
            for student in stop.students:
                if student.fields[6] in cost_centers:
                    to_add = True
        if to_add:
            routes_to_plot.append([route, route_ind])
    plot_routes(routes_to_plot, geocodes, 1.0, 0.98)
    
files_needed = ["Route plan object file", "Geocodes for map data"]    
    
inputs = None
try:
    inputs_save = open("plotting_inputs_save", "rb")
    inputs = pickle.load(inputs_save)
    inputs_save.close()
    print(inputs)
except:
    inputs = ["" for i in range(3)]

root = tkinter.Tk()
textboxes = [None for i in range(3)]
buttons = [None for i in range(2)]

default_font = nametofont("TkDefaultFont")
fontsize = 10
default_font.configure(size=fontsize)
   
def set_file_text(index, text):
    textboxes[index].delete(1.0, tkinter.END)
    textboxes[index].insert(tkinter.END, text)

def set_file(index):
    inputs[index] = askopenfilename()
    set_file_text(index, inputs[index]) 
    
def run_gui(buttons, textboxes):
    global time_elapsed_label, inputs
    
    for i in range(2):
        this_frame = tkinter.Frame(root)
        this_frame.pack(side = tkinter.TOP)
        
        buttons[i] = tkinter.Button(root, text=files_needed[i], command = lambda c=i: set_file(c))
        textboxes[i] = tkinter.Text(root, height = 1)
        
        set_file_text(i, inputs[i])
        buttons[i].pack(in_ = this_frame, side = tkinter.LEFT)
        textboxes[i].pack()
        
    cost_cent_label = tkinter.Label(root, text = 'Cost center IDs (enter in textbox separated by commas)')
    cost_cent_label.pack()
    
    textboxes[2] = tkinter.Text(root, height = 1)
    set_file_text(2, inputs[2])
    textboxes[2].pack()
        
    start_button = tkinter.Button(root, text="Plot Routes", command = plot_routes_gui)
    start_button.pack()
    
    time_elapsed_label = tkinter.Label(root, text = '')
    time_elapsed_label.pack()
    
    root.mainloop()    
    
run_gui(buttons, textboxes)