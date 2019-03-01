#Prepping for use on the UCLA GIS site
#https://gis.ucla.edu/geocoder

def prep_addresses_for_geocoding(filename, addresses, stop_col):
    pb_part = open(filename, 'r')
    
    phonebook_header = pb_part.readline()
    
    for student_record in pb_part.readlines():
        fields = student_record.split(';')
        if len(fields) < stop_col:
            continue
        addr = fields[stop_col]
        if addr.strip() == "":  #no stop
            continue
        #for the census geocoder, need the state
        addr = addr[:-6] + " California," + addr[-6:]
        addresses.add(addr)
        
addresses = set()
prefix = 'C://Users//David//Documents//UCLA//SchoolBusResearch//data//csvs//'
prep_addresses_for_geocoding(prefix+'phonebook_parta.csv', addresses, 18)
prep_addresses_for_geocoding(prefix+'phonebook_partb.csv', addresses, 18)

to_write = open(prefix+('stops_to_geocode_ucla.csv'), 'a')

count = 0
to_write.write("\"ADDRESS\"\n")
for i in addresses:
    count += 1
    to_write.write("\"" + i + "\"\n")
    
to_write.close()