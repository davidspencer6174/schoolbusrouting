from locations import School, Student
from adjustText import adjust_text
import numpy as np
import pickle
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
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
    assert to_plot == None or filename != None, "Must provide a file name if to_plot is not None"
    fig = plt.figure()
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
                                      fontsize = 3, color = 'blue'))
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
                              fontsize = 5, color = 'red'))
        plt.plot([p[0] for p in points], [p[1] for p in points], 'k',
                 linewidth = .1)
        if to_plot != None:
            num_students = 0
            num_schools = 0
            for ind, stop in enumerate(r.stops):
                if ind > 0 and stop.tt_ind != r.stops[ind - 1].tt_ind:
                    message = str(num_students) + " stud, "
                    if num_students == 1:
                        message = "1 stud, "
                    if num_schools == 1:
                        message += "1 sch"
                    else:
                        message += str(num_schools) + " sch"
                    texts.append(plt.text(points[ind - 1][0], points[ind - 1][1],
                                          message, ha='center', va='center',
                                          fontsize = 5))
                    num_students = 0
                    num_schools = 0
                num_schools += 1
                num_students += stop.occs
            message = str(num_students) + " stud, "
            if num_students == 1:
                message = "1 stud, "
            if num_schools == 1:
                message += "1 sch"
            else:
                message += str(num_schools) + " sch"
            texts.append(plt.text(points[len(r.stops) - 1][0],
                                         points[len(r.stops) - 1][1],
                                         message, ha='center', va='center',
                                         fontsize = 5))
    adjust_text(texts, precision = .1, text_from_points = False)
    prefix = ("output//0528presentation//routeplots//")
    plt.axis('off')
    if to_plot == None:
        fig.savefig(prefix + 'spedroutes_all.eps', bbox_inches = 'tight',
                    pad_inches = 0)
    else:
        fig.savefig(prefix + filename, bbox_inches = 'tight',
                    pad_inches = 0)
    #win.getMouse()
    plt.close()
    
    
    

loading = open("output//spedfirsttryb.obj", "rb")
obj = pickle.load(loading)
loading.close()

#vb_routes = []
#for ind in range(len(obj)):
#    r = obj[ind]
#    to_store = False
#    for school in r.schools:
#        to_store = to_store or ("BALBOA" in school.school_name and "LAKE" not in school.school_name)
#        to_store = to_store or ("VINTAGE" in school.school_name)
#    if to_store:
#        vb_routes.append((r, ind))
routes = []
for ind in range(len(obj)):
    r = obj[ind]
    routes.append((r, ind))


geocodes_file = open("data//all_geocodes.csv", "r")
geocodes = []
for code in geocodes_file.readlines():
    latlong = code.split(";")
    if "\n" in latlong[1]:
        latlong[1] = latlong[1][:-2]
    latlong[0] = float(latlong[0])
    latlong[1] = float(latlong[1])
    geocodes.append(latlong)
geocodes_file.close()

xres = 1.0
yres = 0.9
plot_routes(routes, geocodes, xres, yres)
for ind, route_with_ind in enumerate(routes):
    plot_routes(routes, geocodes, xres, yres,
                [route_with_ind[0]], 'sped_routes' + str(ind) + '.eps')
