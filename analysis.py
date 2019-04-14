import main 
import matplotlib.pyplot as plt
import numpy as np


all_schools = list()

for x in range(0, 3):
    for i in range(0, len(total_routes[x])):
        for j in total_routes[x][i]:
            for k in j:
                all_schools.extend(k.school_path)
            
            
all_schools = list(dict.fromkeys(all_schools))
            
plt.hist(test, normed=True, bins=30)