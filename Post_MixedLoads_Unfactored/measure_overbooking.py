import numpy as np
import matplotlib.pyplot as plt

phonebook = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//PhoneBook_10302018.csv', 'r')
buslist = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//UCLA_BusList.csv', 'r')

route = '01'  #can be 01, 02, 03, or 04
bus_col = 10
if route == '03' or route == '04':
    bus_col = 18
#01 and 02 are morning routes; 03 and 04 are afternoon routes

bus_header = buslist.readline()  #skip header line

#the main purpose of the first while loop is to obtain bus capacities
bus_capacities = dict()
while True:
    bus_record = buslist.readline().split(',')
    if len(bus_record) < 2 or bus_record[1] == '':  #empty line
        break
    if bus_record[1][0] == 'V':  #these records have special annotations;
        #all of them have capacity 74 at this time
        bus_capacities[bus_record[0]] = 74
    elif bus_record[1] == '24+1':  #I assume this is 24 bench+1 wheelchair
        bus_capacities[bus_record[0]] = 25
    else:
        bus_capacities[bus_record[0]] = int(bus_record[1])
        
print("Done processing buses")    
buslist.close()

phonebook_header = phonebook.readline()  #skip header line

#helper functino to increment a dict entry or create one if nonexistent
def increment_riders(assigned_rider_counts, bus_id):
    if bus_id in assigned_rider_counts:
        assigned_rider_counts[bus_id] += 1
    else:
        assigned_rider_counts[bus_id] = 1

#now for each rider, we record their assignment to their bus
assigned_rider_counts = dict()
i = 1
while True:
    i += 1
    student_record = phonebook.readline().split(';')
    if len(student_record) < 2:  #done
        break
    #if the student is in a walker or not in the correct route
    if student_record[bus_col-1] == '9500' or (student_record[bus_col+2] != route
        or student_record[bus_col] == ''):
        continue
    if student_record[bus_col] == '8173':
        print(i)
    increment_riders(assigned_rider_counts, student_record[bus_col])
    
print("Done processing riders")
phonebook.close()
    
x = []
y = []
    
for bus_id in assigned_rider_counts.keys():
    if bus_id in bus_capacities.keys():
        x.append(assigned_rider_counts[bus_id])
        y.append(bus_capacities[bus_id])
    else:    #can use these lines to identify missing data
        print(str(assigned_rider_counts[bus_id]) + " students ride on bus " +
              bus_id + ", but bus is not in bus list")
        
x = np.array(x)
y = np.array(y)

identity_function = np.linspace(0, 90, 100)

plt.scatter(x, y, s=10)
plt.plot(identity_function, identity_function, 'g', linewidth=1, markersize=1)
plt.xlabel("Number of students assigned to bus (morning)")
plt.ylabel("Capacity of bus")
plt.axis("Equal")
plt.title("Bus capacities vs. assigned students")


plt.savefig("bus_capacities_plot", dpi=300)