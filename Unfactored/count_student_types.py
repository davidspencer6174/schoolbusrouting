def process_phonebook_part(filename, counts):
    pb_part = open(filename, 'r')
    
    phonebook_header = pb_part.readline()
    
    for student_record in pb_part.readlines():
        fields = student_record.split(';')
        if len(fields) < 5:
            print(student_record)
            continue
        if fields[5] != '':
            if fields[5] in counts:
                counts[fields[5]] += 1
            else:
                counts[fields[5]] = 1
    pb_part.close()
                
counts = dict()
process_phonebook_part('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//csvs//phonebook_parta.csv', counts)
process_phonebook_part('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//csvs//phonebook_partb.csv', counts)

for student_type in counts:
    print("The number of students with designation " + str(student_type)
            + " is " + str(counts[student_type]))