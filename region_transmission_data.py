import csv
from determine_field import determine_field
from ijson_parser import ijson_parser
from trans_to_csv import trans_to_csv

def transmission(year, region):
    " Gives net transmission in MWh for a given year and region."
    field = determine_field("intercon_disp")
    variable_data = ijson_parser(year, field)
    trans_total = [[0 for col in range(5)] for row in range(5)]
    #sorting the trans data into a matrix of total out and in by region
    for i in range(0, len(variable_data[0])):
        var_index = variable_data[0][i]["index"]
        var_value = variable_data[0][i]["value"]
        var_value = round(var_value, 2)
        from_index = int(var_index[0])-1
        to_index = int(var_index[1])-1
        current_value = trans_total[from_index][to_index]
        trans_total[from_index][to_index] = current_value + var_value
        var_value = float(var_value)
    region_id = ["NSW", "QLD", "SA", "TAS", "VIC"]
    region_no = region_id.index(region) + 1
    region_in = 0
    region_out = 0
    #taking the inputted region and determining the net transmission
    for i in range(0, 5):
        region_out = region_out + trans_total[region_no][i]
        region_in = region_in + trans_total[i][region_no]
    region_net = region_out-region_in
    print(region_net, "MWh")
    return trans_total, region_net
    trans_to_csv(trans_total, region_id)
transmission("2030", "NSW")
