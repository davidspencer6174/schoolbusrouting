import pickle
from ds_routestospec import spec_to_ds_routes, spec_to_ds_route, ds_route_to_spec
from ds_setup import setup_ds_students
from wh_routestospec import convert_route_to_common, convert_route_from_common
import copy

with open('/Users/cuhauwhung/Desktop/one_unpacked_routes.pickle', 'rb') as f:
    number_one = pickle.load(f)

with open('/Users/cuhauwhung/Desktop/two_unpacked_routes.pickle', 'rb') as f:
    number_two = pickle.load(f)


def disp(route):
    print(route.schools_path)
    print(route.stops_path)


def is_equal(route_1, route_2):
    
    schools_1 = [x[0] for x in route_1.schools_path]
    schools_2 = [x[0] for x in route_2.schools_path]
    
    pairs_1 = [(x[0], x[2]) for x in route_1.stops_path]
    pairs_2 = [(x[0], x[2]) for x in route_2.stops_path]
    
    if schools_1 == schools_2 and pairs_1 == pairs_2:
        return True
    else:
        return False

converted = list()


prefix = "/Users/cuhauwhung/Google Drive (cuhauwhung@g.ucla.edu)/Masters/Research/school_bus_project/Data/csvs/"
output = setup_ds_students([prefix+'phonebook_parta.csv',
                         prefix+'phonebook_partb.csv'],
                         prefix+'all_geocodes.csv',
                         prefix+'stop_geocodes_fixed.csv',
                         prefix+'school_geocodes_fixed.csv',
                         prefix+'bell_times.csv')

ds_students = output[0]
ds_schools_ds_students_map = output[1]
all_ds_schools = output[2]


for idx, r in enumerate(number_two):
    new = convert_route_to_common(copy.deepcopy(r))
    ds_route = spec_to_ds_route(new, ds_students, ds_schools_ds_students_map, all_ds_schools)
    new_inter = ds_route_to_spec(ds_route)
    new_r = convert_route_from_common(new_inter)
    
    if is_equal(r, new_r):
        pass
    else:
        disp(r) 
        print('\n')
        disp(new_r)
        print('---------')

        converted.append(r)
        print(idx)
