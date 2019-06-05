from wh_routestospec import wh_routes_to_spec, spec_to_wh_routes
from ds_routestospec import ds_routes_to_spec, spec_to_ds_routes
from ds_utils import improvement_procedures

# TODO: CHECK IF THIS ACTUALLY WORKS
def convert_and_improve(routes):
    print("Converting and improving")
    spec_routes = wh_routes_to_spec(routes)
    ds_routes = spec_to_ds_routes(spec_routes)
    improved_ds_routes = improvement_procedures(ds_routes)
    improved_spec_routes = ds_routes_to_spec(improved_ds_routes)
    wh_routes = spec_to_wh_routes(improved_spec_routes)
    return wh_routes