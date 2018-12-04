import ijson

def ijson_parser(ijson_index):
    filename = "ISP_S_nc_sol_unzipped.json"
    with open(filename, 'r') as f:
        objects = ijson.items(f,ijson_index)
        variable_list = list(objects)
    print(variable_list)
    return(variable_list)
#ijson_parser(2020,"hello")
#2020.sets.regions.fuel_tech_in_zones
