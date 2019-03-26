"""Functions for determination of the reserve margin from sqlite data."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IO_functions import sql_reader

#defining global variables
NOARG = None
YRS = [2020, 2025, 2030, 2035, 2040, 2045]
REG = 'NSW'

def remove_other_regions(frame):
    """ Removes data for other regions from either the gen or cap dataframes"""
    #defines zones within each regions and sets the zones to be included
    qld = [1, 2, 3, 4]
    nsw = [5, 6, 7, 8]
    vic = [9, 10, 11, 12]
    s_a = [13, 14, 15]
    tas = [16]
    if REG == 'QLD':
        zones = qld
    elif REG == 'NSW':
        zones = nsw
    elif REG == 'VIC':
        zones = vic
    elif REG == 'SA':
        zones = s_a
    elif REG == 'TAS':
        zones = tas
    else:
        return print('Input one of QLD, NSW, VIC, SA or TAS as a string.')
    #filters for zones within the region
    frame = frame[frame['ntndp_zone_id'].isin(zones)]
    return frame

def get_gen_data(start_year=NOARG, end_year=NOARG):
    """ Loads generation data into pandas frame."""
    base_query = "select * from generation"
    first_day = "-01-01 00:00:00'"
    last_day = "-31-12 00:00:00'"
    #checking year range input and adjusting sql query
    if start_year is NOARG:
        query = base_query
        sel_years = YRS
    elif (start_year in YRS and end_year is NOARG):
        query = base_query + " where timestable between '" + str(start_year) \
        + first_day + " and '" + str(start_year) + last_day
        sel_years = [start_year]
    elif (start_year in YRS and end_year in YRS):
        query = base_query + " where timestable between '" + str(start_year) \
        + first_day + " and '" + str(end_year) + last_day
        sel_years = np.arange(start_year, end_year+5, 5)
    else:
        return print("Inputted year/s are not of the simulated range. \
Please input one of:", YRS)
    #loading generation into frame
    generation = sql_reader(query)
    generation = remove_other_regions(generation)
    generation = generation.groupby(["timestable"]).sum()
    generation = generation.drop(["ntndp_zone_id", "technology_type_id"], axis=1)
    return generation, sel_years

def get_cap_data(sel_years):
    """ Loads capacity data into pandas frame."""
    #loads capacity data into frame
    capacity = sql_reader('select * from existing_capacity')
    capacity = remove_other_regions(capacity)
    mod_years = len(YRS)
    no_sel_yr = len(sel_years)
    no_cap_yr = int(len(capacity)/mod_years)
    #removes other year data, years aren't specified in the db so data is split
    # and checked against the selected years then removed if not within the range
    for i in range(0, no_sel_yr+1):
        if YRS[i] not in sel_years:
            capacity = capacity.iloc[no_cap_yr:]
        else:
            break
    for i in range(1, no_sel_yr+1):
        if YRS[mod_years-i] not in sel_years:
            capacity = capacity.iloc[:-no_cap_yr]
        else:
            break
    #summing to total capacity
    total_capacity = [None]*len(sel_years)
    for i in enumerate(sel_years):
        total_capacity[i[0]] = capacity.iloc[:no_cap_yr]["value"].sum()
        capacity = capacity.iloc[no_cap_yr:]
    return total_capacity

def calc_margin(total_capacity, generation, sel_years):
    """Calculates the reserve margin, divdes capacity by generation."""
    reserve_margin = [None]*len(sel_years)
    for i in enumerate(sel_years):
        current_year = str(i[1])
        current_cap = total_capacity[i[0]]
        reserve_margin[i[0]] = generation[generation.index.str.contains(current_year)].copy()
        reserve_margin[i[0]].loc[:, "value"] = reserve_margin[i[0]]["value"].divide(current_cap)
    return reserve_margin

def calc_stats(reserve_margin, sel_years):
    """ Finds min margin and time, and the mean margin for each year."""
    min_mrg = [None]*len(sel_years)
    min_time = [None]*len(sel_years)
    rsv_mrg_mean = [None]*len(sel_years)
    for i in enumerate(sel_years):
        rsv_mrg_mean[i[0]] = reserve_margin[i[0]].mean()["value"]
        min_time[i[0]] = reserve_margin[i[0]].idxmax()["value"]
        min_mrg[i[0]] = reserve_margin[i[0]].max()["value"]
    return min_time, min_mrg, rsv_mrg_mean

def yearly_plots(reserve_margin, sel_years):
    """Makes yearly plots for of the reserve margin. This is very slow. Done
    out of interest more than anything."""
    for i in enumerate(reserve_margin):
        current_time_series = i[1].index
        current_margin = i[1].value
        plt.plot(current_time_series, current_margin, linewidth=0.1)
        filename = str(sel_years[i[0]]) + "_reserve_margin.png"
        plt.savefig(filename)
        plt.clf()
        #plt.show()

def value_test():
    """ Simple value checks for loaded data."""
    generation = get_gen_data()
    assert generation.min()["value"] > 0, "Generation has zero valued member."
    capacity = get_cap_data(YRS)
    assert min(capacity) > 0, "Capacity has zero valued member."
    reserve_margin = calc_margin(capacity, generation, YRS)
    assert min(reserve_margin) > 0, "Reserve margin has zero valued member."

#calling each of the functions and generating reserve_margin statistics
def rsv_main(year1, year2):
    [GEN, YRS] = get_gen_data(year1, year2)
    CAP = get_cap_data(YRS)
    RSV_MRG = calc_margin(CAP, GEN, YRS)
    [MIN_T, MIN_MARG, MARG_MEAN] = calc_stats(RSV_MRG, YRS)
    RSV_INFO = {'min_t': MIN_T, 'min_marg': MIN_MARG, 'MARG_MEAN': MARG_MEAN}
    RSV_INFO = pd.DataFrame(data=RSV_INFO)
    return RSV_INFO
