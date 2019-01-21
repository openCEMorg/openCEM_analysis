import numpy as np
import matplotlib.pyplot as plt
import pytest
from si_prefix import si_format
from IO_functions import sql_reader, is_date

#defining global variables
NOARG = None
REGIONS = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']

def get_trans_data(start_date=NOARG, end_date=NOARG):
    """ Loads interconnector data for specified dates. To only input end_date \
    start date must specified as 0."""
    #defing sql query based on date input to function
    base_query = "select * from interconnector"
    #no date input
    if start_date is NOARG:
        query = base_query
    #only starting date input
    elif (is_date(start_date) and end_date is NOARG):
        query = base_query + " where not (timestamp < '" + start_date + " 00:00:00')"
    #only end_date input
    elif (start_date == 0 and is_date(end_date)):
        query = base_query + " where not (timestamp > '" + end_date + " 00:00:00')"
    #both start and end date specified
    elif (is_date(start_date) and is_date(end_date)):
        query = "select * from interconnector where timestamp between '" + \
        start_date + " 00:00:00'" + " and '" + end_date + " 00:00:00'"
    #dates not correctly specified
    else:
        error_statement = "Date range is of incorrect format. \
                           Please input as 'YYYY-MM-DD'."
        return error_statement
    #load date in pandas frame
    trans_data = sql_reader(query)
    trans_data = trans_data[trans_data.value > 0]
    return trans_data

def get_net_data(trans_data):
    """ Calculates net and region based trade from transmission data."""
    #sum zone and technolog values within the same region
    grouped = trans_data['value'].groupby(trans_data['region_id'])
    out_trans = grouped.sum()
    grouped = trans_data['value'].groupby(trans_data['technology_type_id'])
    in_trans = grouped.sum()
    #check whether all regions import and exported
    if len(in_trans) == len(out_trans) == 5:
        net = np.array(out_trans - in_trans)
    #if not fill regions which didn't trade with zero values
    else:
        full_regions = {1, 2, 3, 4, 5}
        in_trans_reg = set(in_trans.index)
        out_trans_reg = set(out_trans.index)
        in_trans_vec = np.array([None]*5)
        out_trans_vec = np.array([None]*5)
        none_in = in_trans_reg ^ full_regions
        none_out = out_trans_reg ^ full_regions
        for i in enumerate(out_trans):
            out_trans_vec[out_trans.index[i[0]]-1] = i[1]
        for i in enumerate(in_trans):
            in_trans_vec[in_trans.index[i[0]]-1] = i[1]
        if none_in != {}:
            for i in enumerate(none_in):
                in_trans_vec[i[1]-1] = 0
        elif none_out != {}:
            for i in enumerate(none_out):
                out_trans_vec[i[1]-1] = 0
        else:
            print("Why are we here")
        net = out_trans_vec - in_trans_vec
        net = net*(10**6)
        in_trans = in_trans_vec
        out_trans = out_trans_vec
    return net, in_trans, out_trans

def trans_net_results(net):
    """Prints breakdown of net transmission by state in correct units."""
    for i in enumerate(net):
        current_region = REGIONS[i[0]]
        if i[1] < 0:
            trade = "imports"
        elif i[1] > 0:
            trade = "exports"
        else:
            print(current_region, "had no net trade over this time period.")
            return
        current_trade = si_format(i[1], precision=3)
        print(current_region, "had net", trade, "of", current_trade, "Wh over this time period.")
    return

def trans_to_csv(trans_data):
    """Outputs csv of full transmission data."""
    trans_data.columns = ["Region From", "Region To", "Timestamp", \
                          "Energy Transferred Between Regions (MWh)"]
    trans_data.to_csv('transmissions_data.csv')

def trans_plot(in_trans, out_trans):
    """ Makes bar plot of region based imports and exports."""
    in_trans = in_trans*(-1)
    in_trans = in_trans*10**(-3)
    out_trans = out_trans*10**(-3)
    plt.figure()
    plot_ax = plt.subplot(111)
    #plot imports as negative bars, exports as positive
    imports = plot_ax.bar(REGIONS, in_trans, width=1, color='r')
    exports = plot_ax.bar(REGIONS, out_trans, width=1, color='b')
    plot_ax.set_ylabel('Trade (GWh)')
    plot_ax.legend([exports, imports], ["Exports", "Imports"])
    plt.show()

def value_test():
    """ Tests that imports and exports sum to zero correctly and that values \
    match those already listed on the website."""
    trans_data = get_trans_data()
    [net, trans_in, trans_out] = get_net_data(trans_data)
    assert round(sum(trans_in), 4) == round(sum(trans_out), 4), \
                                "Sum of exports do not equal sum of imports."
    assert round(sum(net)) == 0, "Net trade values do not sum to zero."
    #matching unit prefixes
    trans_in = trans_in*10**(-6)
    trans_out = trans_out*10**(-6)
    net = net*10**(-6)
    #matching precision to that of website
    trans_in = round(trans_in, 3)
    trans_out = round(trans_out, 3)
    net = net.round(3)
    #values taken from website for the N_cp scenario
    import_ref = [7.730, 0.133, 5.502, 0.072, 0.869]
    export_ref = [0.419, 5.009, 0.181, 0.397, 8.295]
    net_ref = [-7.311, 4.876, -5.321, 0.325, 7.426]
    inout_error_level = 0.0021
    net_error_level = 0.005
    assert (trans_in - import_ref < inout_error_level).all(), \
                "Imports do not match website values."
    assert (trans_out - export_ref < inout_error_level).all(), \
                "Exports do not match website values."
    assert (net - net_ref < net_error_level).all(), \
                "Net trade does not match website values."
TRANS = get_trans_data()
[NET, IN, OUT] = get_net_data(TRANS)
trans_net_results(NET)
trans_plot(IN, OUT)
value_test()
