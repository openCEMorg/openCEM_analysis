#this function is to output a csv with only the transmission data for the
#given year and region
#currently does not work
import csv
from ijson_parser import ijson_parser
from determine_field import determine_field

#currently, the values aren't being read into the list correctly
# error AttributeError: 'NoneType' object has no attribute 'append'
# when appending a list of values line 31

def transmission_csv(year, region):
    field = determine_field("intercon_disp")
    ijson_index = year + "." + field + "." + "intercon_disp"
    variable_data = ijson_parser(ijson_index)
    end_index = len(variable_data[0])
    variable_list = [["From", "To", "Time", "Value"]]
    #taking the data and turning into a list of 4 element lists
    for i in range(0, end_index):
        current_data = [0, 0, 0, 0]
        current_data[0] = variable_data[0][i]["index"][0]
        current_data[1] = variable_data[0][i]["index"][1]
        current_data[2] = variable_data[0][i]["index"][2]
        current_data[3] = float(variable_data[0][i]["value"])
        #only taking non-zero values for the given region
        in_region = ((current_data[0] == region) or (current_data[1] == region))
        store_data = (in_region and (current_data[3] > 0))
        print(current_data)
        if store_data:
            variable_list = variable_list.append(current_data)
        else:
            continue
    fname = year + 'transmission_data.csv'
    with open(fname, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(variable_list)
transmission_csv("2020", 1)
