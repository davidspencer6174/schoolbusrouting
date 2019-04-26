import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import statistics



stud_times = list()
for i in routes_returned:
    for j in routes_returned[i]:
        for k in j:
            for k in k.students:
                stud_times.append(k.time_on_bus)
stud_times.sort()

stud_times = [round(x/60,2) for x in stud_times]



statistics.mean(stud_times)
plt.hist(stud_times, normed=False, bins=15)
plt.ylabel('Number of Students')
plt.xlabel('Estimated Travel Times (minutes)')

