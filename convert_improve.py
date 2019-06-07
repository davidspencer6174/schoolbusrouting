from wh_routestospec import wh_routes_to_spec, spec_to_wh_routes
from ds_routestospec import ds_routes_to_spec, spec_to_ds_routes
from ds_utils import improvement_procedures

# Convert routes between formats and perform David's post-improv procedures
def convert_and_improve(routes):
    print("Converting and improving")
    routes = clean_all_routes(routes)
    spec_routes = wh_routes_to_spec(routes)
    ds_routes = spec_to_ds_routes(spec_routes)
    improved_ds_routes = improvement_procedures(ds_routes)
    improved_spec_routes = ds_routes_to_spec(improved_ds_routes)
    wh_routes = spec_to_wh_routes(improved_spec_routes)

    if len(routes) == len(wh_routes):
        print("FIN: No improvements were made")
    else:
        print(" ------------------------------------------- FIN: Improvements")

    return wh_routes

# Clean routes, remove schools that do not need to be visited from routes 
def clean_all_routes(routes):
    cleaned_routes = list()
    for route in routes:
        route.clean_route()
        cleaned_routes.append(route)
    return cleaned_routes