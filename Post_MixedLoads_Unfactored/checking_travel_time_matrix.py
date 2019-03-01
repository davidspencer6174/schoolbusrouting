import numpy as np
import random as random
import math

travel_times = np.load("C://Users//David//Documents//UCLA//SchoolBusResearch" +
                       "//data//travel_time_matrix.npy")

print(str(travel_times.shape) + " is the shape of the matrix")
print(str((travel_times == 0).sum()) + " zeros in the matrix")

N = travel_times.shape[0]

#see how often triangle inequality holds
violations = 0
trials = 100000
for i in range(trials):
    l1 = math.floor(random.random()*N)
    l2 = math.floor(random.random()*N)
    l3 = math.floor(random.random()*N)
    #There seem to be some rounding issues, so test for >1s violations
    if travel_times[l1][l2] + travel_times[l2][l3] < travel_times[l1][l3] - 1:
        violations += 1
        print("Triangle inequality violation found")
        print("Locations " + str(l1) + " " + str(l2) + " " + str(l3))
        print(str(travel_times[l1][l2]) + " " + str(travel_times[l2][l3])
            + " " + str(travel_times[l1][l3]))
        
print("Triangle inequality is violated " + str(violations/trials*100)
      + "% of the time on " + str(trials) + " trials.")

duplicate_pairs = 0
for i in range(N):
    for j in range(i):
        if travel_times[i][j] == 0:
            if np.max(np.abs(travel_times[i]-travel_times[j])) < 1:
                duplicate_pairs += 1
            
print("Number of approximate duplicate pairs of rows found: " + str(duplicate_pairs))

print("L1 norm of matrix: " + str(np.sum(travel_times)))
skew_sym = (travel_times-np.transpose(travel_times))/2
print("L1 norm of skew-symmetric part: " + str(np.sum(np.abs(skew_sym))))