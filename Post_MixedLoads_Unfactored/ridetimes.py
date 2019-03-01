import numpy as np
import matplotlib.pyplot as plt

phonebook = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//PhoneBook_10302018.csv', 'r')
belltimelist = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//UCLA_BellSchedule2018-19.csv', 'r')

route = '01'  #Bell times are only given for the morning routes, so 01 or 02

phonebook_header = phonebook.readline()  #skip header line

def timemins(time_string):  #bit of a hack to compute minutes since midnight
    pieces = time_string.split(':')
    minutes = int(pieces[1][:2])  #minutes
    minutes += 60*int(pieces[0])  #hours
    if 'p' in pieces[1].lower():  #PM
        minutes += 12*60
    return minutes

bell_header = belltimelist.readline()  #skip header

#create dictionary of cost centers (essentially, schools) with bell times
bell_times = dict()
while True:
    bell_record = belltimelist.readline().split(',')
    if len(bell_record) < 2:
        break
    bell_times[bell_record[3]] = timemins(bell_record[4])
    
print("Done processing bell times")
belltimelist.close()

#for each rider, determine difference between pickup/dropoff and bell time
times = []
unfound_cost_centers = set()
while True:
    student_record = phonebook.readline().split(';')
    if len(student_record) < 2:  #done
        break
    #if the student is in a walker or not in the correct route
    if student_record[9] == '9500' or (student_record[12] != route
        or student_record[10] == ''):
        continue
    pickup_time = timemins(student_record[14])
    student_cost_center = student_record[0]
    if student_cost_center not in bell_times:
        unfound_cost_centers.add(student_cost_center)
        continue
    times.append(bell_times[student_cost_center] - pickup_time)
    
print("Done processing riders")
print("Unlocated cost centers: " + str(unfound_cost_centers))
phonebook.close()
    
times = np.array(times)
plt.hist(times, bins=np.arange(max(times)//5+1)*5)  #binning in groups of 5
plt.xlabel("Difference between bell time and pickup time (5 min bins)")

#unbinned
    
#turn times into counts of times
#counts = np.zeros(max(times) + 1)
#for i in times:
#    counts[i] += 1

#plt.plot(np.linspace(0, max(times), max(times) + 1), counts)

#plt.xlabel("Difference between bell time and pickup time (min)")
plt.ylabel("Number of students")
plt.title("Counts of ride times for route " + route)


plt.show()