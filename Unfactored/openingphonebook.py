f = open('C://Users//David//Documents//UCLA//SchoolBusResearch'+
         '//data//PhoneBook_10092018.csv', 'r')

s = set()

i = 0
for line in f:
    cols = line.split(";")
    s.add(cols[15].strip())
    if len(cols[15].strip()) > 3:
        i += 1
    
print("Number of students riding: " + str(i))
print("Number of unique stops: " + str(len(s)))

l = []
for string in s:
    l.append(string)
    
l.sort()

#for i in range(1000):
#    print(l[i])