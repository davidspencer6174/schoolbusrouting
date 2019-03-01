import numpy as np
import matplotlib.pyplot as plt
import operator

phonebook = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//PhoneBook_10302018.csv', 'r')
buslist = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//UCLA_BusList.csv', 'r')

route = '04'  #can be 01, 02, 03, or 04
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

#helper function to increment a dict entry or create one if nonexistent
def increment_riders(assigned_rider_counts, bus_id):
    if bus_id in assigned_rider_counts:
        assigned_rider_counts[bus_id] += 1
    else:
        assigned_rider_counts[bus_id] = 1

#now for each rider, we record their assignment to their bus
assigned_rider_counts = dict()
#also record their zipcode
zipcode_counts = dict()
while True:
    student_record = phonebook.readline().split(';')
    if len(student_record) < 2:  #done
        break
    #if the student is in a walker or not in the correct route
    if student_record[bus_col-1] == '9500' or (student_record[bus_col+2] != route
        or student_record[bus_col] == ''):
        continue
    increment_riders(assigned_rider_counts, student_record[bus_col])
    zipcode = int(student_record[bus_col+6].split(' ')[-1])
    increment_riders(zipcode_counts, zipcode)
    
print("Done processing riders")
phonebook.close()

phonebook = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//PhoneBook_10092018.csv', 'r')
phonebook_header = phonebook.readline()

overbooked_zip_counts = dict()
while True:
    student_record = phonebook.readline().split(';')
    if len(student_record) < 2:  #done
        break
    #if the student is in a walker or not in the correct route
    if student_record[bus_col-1] == '9500' or (student_record[bus_col+2] != route
        or student_record[bus_col-1] == ''):
        continue
    bus = student_record[bus_col-1]
    if bus not in bus_capacities.keys() or bus not in assigned_rider_counts.keys():
        continue
    if assigned_rider_counts[bus] > bus_capacities[bus]:
        zipcode = int(student_record[bus_col+6].split(' ')[-1])
        increment_riders(overbooked_zip_counts, zipcode)
        
sorted_zips = sorted(zipcode_counts.items(), key=operator.itemgetter(1))[::-1]
sorted_overbook_zips = sorted(overbooked_zip_counts.items(),
                              key=operator.itemgetter(1))[::-1]
print("Count of all students in zipcode")
print(sorted_zips)
print("Count of # of students on overbooked buses in zipcode")
print(sorted_overbook_zips)
    
print("Zip codes where at least 15% of students are on overbooked buses:")
for i in overbooked_zip_counts.keys():
    val = overbooked_zip_counts[i]/zipcode_counts[i]
    #print(str(i) + " " + str(val))
    if val >= .15:
        print(str(i) + " " + str(val))