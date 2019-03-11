import constants

#Used to get the data into a full address format        
def californiafy(address):
    return address[:-6] + " California," + address[-6:]

#Bit of a hack to compute seconds since midnight
def timesecs(time_string):
    pieces = time_string.split(':')
    if len(pieces) < 2:
        return 100000
    minutes = int(pieces[1][:2])  #minutes
    minutes += 60*int(pieces[0])  #hours
    if 'p' in pieces[1].lower():  #PM
        minutes += 12*60
    return minutes*60

#Determines a closest pair of locations in from_iter and to_iter
#from_iter and to_iter should both be iterables of Students and/or Schools
#optionally, can require a specific age type if to_iter has Students
def closest_pair(from_iter, to_iter, age_type = None):
    opt_dist = 100000
    opt_from_loc = None
    opt_to_loc = None
    for from_loc in from_iter:
        for to_loc in to_iter:
            if (constants.TRAVEL_TIMES[from_loc.tt_ind,
                                       to_loc.tt_ind] < opt_dist and
                (age_type == None or to_loc.type == age_type)):
                opt_dist = constants.TRAVEL_TIMES[from_loc.tt_ind,
                                                  to_loc.tt_ind]
                opt_from_loc = from_loc
                opt_to_loc = to_loc
    return opt_from_loc, opt_to_loc