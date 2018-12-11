import ijson

def ijson_parser(year, field):
    """ Parses section of the json file using ijson based on given year and field."""
    #generating index within json file
    ijson_index = year + "." + field + "." + "intercon_disp"
    filename = "ISP_S_nc_sol_unzipped.json"
    #loading json data
    with open(filename, 'r') as json_file:
        objects = ijson.items(json_file, ijson_index)
        variable_list = list(objects)
    return variable_list
