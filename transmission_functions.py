import numpy as np
import math
import matplotlib.pyplot as plt
from IO_functions import sql_reader, is_date
from dateutil.parser import parse

#defining global variables
NOARG = None
REGIONS = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']

def get_date_query(base_query, start_date, end_date):
    where_query = " where "
    end_obj = parse(end_date, fuzzy=True)
    start_obj = parse(start_date, fuzzy=True)
    start_string = start_date = str(start_obj.year) + "-" + start_obj.strftime('%m') + "-" \
    + start_obj.strftime('%d') + " 00:00:00'"
    end_string = str(end_obj.year) + "-" + end_obj.strftime('%m') + "-" \
    + end_obj.strftime('%d') + " 00:00:00'"
    query = base_query + where_query + "timestamp between '" + start_string + \
    " and '" + end_string
    return query

def get_trans_data(region=NOARG, start_date=NOARG, end_date=NOARG):
    base_query = "select * from interconnector"
    if region is NOARG or start_date is NOARG:
        trans_data = sql_reader(base_query)
        region = 'ALL'
    elif region in REGIONS or region == 'ALL' or isdate(region):
        pass
    else:
        error_statement = "First argument has not been correctly inputted\
        If inputting a region please input as one of 'NSW', 'QLD', 'VIC', 'SA'\
        , 'TAS' or 'ALL'. If inputting a date please input in some format such\
         as 'YYYY-MM-DD'."
        return error_statement
    if is_date(region) and is_date(start_date):
        trans_data = sql_reader(get_date_query(base_query, region, start_date))
    elif is_date(start_date) and is_date(end_date):
        trans_data = sql_reader(get_date_query(base_query, start_date, end_date))
    else:
        error_statement = "Either two dates have not been inputted as \
        arguments or one of the dates cannot be recognised as a date. Please \
        input two dates in a format such as 'YYYY-MM-DD'"
        return error_statement
    state_cond = {1: "NSW", 2: "QLD", 3: "SA", 4: "TAS", 5: "VIC"}
    state_cond = {"region_id":state_cond, "technology_type_id":state_cond}
    trans_data = trans_data.replace(state_cond)
    trans_data = trans_data.loc[(trans_data != 0).all(1)]
    if region == 'ALL':
        pass
    else:
        trans_data = trans_data.loc[(trans_data == region).any(1)]
    return trans_data, region

def get_trade(trans_data, region):
    exports = trans_data[trans_data["region_id"] == region]
    imports = trans_data[trans_data["technology_type_id"] == region]
    exports = exports.drop("region_id", axis=1)
    imports = imports.drop("technology_type_id", axis=1)
    exports = exports.groupby("technology_type_id").sum()
    imports = imports.groupby("region_id").sum()

    return exports, imports



def plot_single_region(exports, imports, region):
    plt.clf()
    trade_ratio = math.log(imports.value.sum())/math.log(exports.value.sum())
    if trade_ratio >= 1:
        exports_radius = 1.15/trade_ratio
        imports_radius = 1.15
    else:
        exports_radius = 1.15
        imports_radius = 1.15*trade_ratio
    exports.loc[len(exports)+1] = exports.value.sum()
    imports.loc[len(imports)+1] = imports.value.sum()
    color_map = {"NSW": "b", "QLD": "g", "SA": "r", "TAS": "c", "VIC": "y", 2: "k", 3: "k", 4:"k"}
    exports_colors = [color_map.get(x, x) for x in exports.index]
    imports_colors = [color_map.get(x, x) for x in imports.index]
    imports_total = imports.value.sum()
    i = [0]
    def imports_value(val):
        if i[0] == len(imports)-1:
            a = None
        else:
            a = imports.iloc[i[0]%len(imports),i[0]//len(imports)]
            a = a/1000
            a = np.round_(a, decimals=3)
        i[0] += 1
        return(a)
    imports_pie = plt.pie(imports, counterclock=True, radius=imports_radius, colors=imports_colors, autopct=imports_value, pctdistance=1.16)
    plt.title("Imports", y = 1.007)
    plt.xlabel("Exports", labelpad=20)
    imports_pie[0][len(imports)-1].set_alpha(0)
    i[0]=0
    def exports_value(val):
        if i[0] == len(exports)-1:
            b = None
        else:
            b = exports.iloc[i[0]%len(exports),i[0]//len(exports)]
            b = b/1000
            b = np.round_(b, decimals=3)
        i[0] += 1
        return(b)
    exports_pie = plt.pie(exports, counterclock=False, radius=exports_radius, colors=exports_colors, autopct=exports_value, pctdistance=1.16)
    exports_pie[0][len(exports)-1].set_alpha(0)
    if len(exports.index) > len(imports.index):
        legend_string = list(exports.index[0:len(exports.index)-1])
    else:
        legend_string = list(imports.index[0:len(imports.index)-1])
    plt.legend(legend_string)
    fname = region + "_trade.png"
    plt.savefig(fname, quality=80)

def plot_one_pie(trade_frame, region, what_trade):
    plt.clf()
    trade_frame.loc[len(trade_frame)+1] = trade_frame.value.sum()
    color_map = {"NSW": "b", "QLD": "g", "SA": "r", "TAS": "c", "VIC": "y", 2: "k", 3: "k", 4:"k"}
    frame_colors = [color_map.get(x, x) for x in trade_frame.index]
    plt.title(what_trade)
    frame_pie = plt.pie(trade_frame, counterclock=False, colors=frame_colors, radius=1.15)
    frame_pie[0][len(trade_frame)-1].set_alpha(0)
    legend_string = list(trade_frame.index[0:len(trade_frame.index)-1])
    plt.legend(legend_string)
    fname = region + "_trade.png"
    plt.savefig(fname, quality=80)

def get_trade_array(trans_data, region):
    if region in REGIONS:
        exports, imports = get_trade(trans_data, region)
        plot_single_region(exports, imports, region)
    else:
        num_regions = len(REGIONS)
        trade_array = np.zeros((num_regions, num_regions))
        for num, region_i in enumerate(REGIONS):
            exports, imports = get_trade(trans_data, region_i)
            if imports.empty and exports.empty:
                print("No trade for ", region_i)
            elif exports.empty:
                plot_one_pie(imports, region_i, "Imports")
            elif imports.empty:
                plot_one_pie(exports, region_i, "Exports")
            else:
                plot_single_region(exports, imports, region_i)
            imports = imports[:-1]
            exports = exports[:-1]
            for index, state in enumerate(imports.index):
                to_id = REGIONS.index(region_i)
                from_id = REGIONS.index(state)
                trade_array[from_id, to_id] = imports.value[index]
            for index, state in enumerate(exports.index):
                to_id = REGIONS.index(state)
                from_id = REGIONS.index(region_i)
                trade_array[from_id, to_id] = exports.value[index]
    return

TRANS, REG = get_trans_data("ALL", "2020-01-01", "2035-04-07")
get_trade_array(TRANS, REG)
