import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from dateutil.parser import parse
from datetime import timedelta
from IO_functions import sql_reader, is_date
""" Set of functions which make basic time series plots of generation data"""

NOARG = None
def state_condition():
    """ Creates a condition which allows for zone values to be mapped to \
    regions"""
    qld = [1, 2, 3, 4]
    nsw = [5, 6, 7, 8]
    vic = [9, 10, 11, 12]
    s_a = [13, 14, 15]
    tas = [16]
    d_qld = dict.fromkeys(qld, "QLD")
    d_nsw = dict.fromkeys(nsw, "NSW")
    d_vic = dict.fromkeys(vic, "VIC")
    d_sa = dict.fromkeys(s_a, "SA")
    d_tas = dict.fromkeys(tas, "TAS")
    state_cond = {**d_qld, **d_nsw, **d_vic, **d_sa, **d_tas}
    return state_cond

def tech_legend(frame):
    """ Takes tech id's included in df and generates lost of those used to be\
    included in plot legend."""
    tech_legend = ['Biomass', 'CCGT', 'CCGT CCS', 'Coal SC', 'Coal SC CCS', \
    'Brown Coal SC', 'Brown Coal SC CCS', 'OCGT', 'Solar PV DAT', 'Solar PV FFP',\
    'Solar PV SAT', 'Wind', 'CST 6h', 'PHES 6h', 'Battery 2h', 'Recip Engine',\
    'Wind H', 'Hydro', 'Gas (Thermal)', 'Pumps']
    used_tech = frame.columns.values
    tech_id = [None]*len(used_tech)
    for j, tech_index in enumerate(used_tech):
        tech_id[j] = tech_legend[tech_index-1]
    return tech_id

def get_cap_tech_data(sel_years):
    """ Loads capacity data into pandas frame based on given years."""
    YRS = [2020, 2025, 2030, 2035, 2040, 2045] #modelled years
    #loads capacity data into frame
    capacity = sql_reader('select * from existing_capacity')
    mod_years = len(YRS)
    no_sel_yr = len(sel_years)
    no_cap_yr = int(len(capacity)/mod_years)
    #removes other year data, years aren't specified in the db so data is split
    # and checked against the selected years then removed if not within the range
    new_capacity = [None]*no_sel_yr
    no_state = [None]*no_sel_yr
    j = 0
    for i in range(0, no_sel_yr):
        if YRS[i] not in sel_years:
            capacity = capacity.iloc[no_cap_yr:]
        else:
            new_capacity[j] = capacity.iloc[0:no_cap_yr]
            capacity = capacity.iloc[no_cap_yr:]
            j = j + 1
    #maps zones to regions
    state_cond = state_condition()
    for i in range(0, no_sel_yr):
        new_capacity[i]["ntndp_zone_id"] = new_capacity[i]["ntndp_zone_id"].map(state_cond)
        new_capacity[i] = new_capacity[i].groupby(["ntndp_zone_id", "technology_type_id"]).sum()
        new_capacity[i] = new_capacity[i].loc[(new_capacity[i] != 0).any(axis=1)]
        no_state[i] = new_capacity[i].groupby("technology_type_id").sum()
    return no_state

def plot_cap_by_tech(no_state, years):
    """Makes stacked bar plot of yearly generation by technology."""
    #rearranging into format for stacked bar plot
    bar_frame = no_state[0]
    for i in range(1, len(years)):
        left = str(years[i-1])
        right = str(years[i])
        bar_frame = bar_frame.join(no_state[i], how='outer', lsuffix=left, rsuffix=right)
    bar_frame = bar_frame.transpose()
    #making stacked bar plot
    tech_id  = tech_legend(bar_frame)
    fontP = FontProperties()
    fontP.set_size('small') #smaller font because the legend is large
    bar_frame.plot(kind='bar', stacked=True)
    plt.xlabel('Year')
    plt.ylabel('Capacity(MW)')
    sub_ax = plt.subplot(111)
    box = sub_ax.get_position()
    #resizing figure area to fit the legend
    sub_ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])
    sub_ax.set_xticklabels([str(i) for i in years])
    #making the legend
    sub_ax.legend(labels=tech_id, loc='best', bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=fontP)
    #adjusting box size so legend and xlabel aren't cut out
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.gcf().subplots_adjust(right=0.7)
    plt.savefig('Yearly_Capacity.png', quality=80)

def get_cap_time_data(start_date, time_period, region=NOARG):
    """Gets time slice generation data to be plotted. Time period must be \
    specified. """
    #generating sql query based on user input
    base_query = "select * from generation"
    where_query = " where"
    if is_date(start_date):
        start_obj = parse(start_date, fuzzy=True)
        #accounting for when time period spills over end of year
        if start_obj.month == 12 and time_period > (31 - start_obj.day):
            time_period = 31 - start_obj.day
        else:
            pass
        end_obj = start_obj + timedelta(days=time_period)
        start_date = str(start_obj.year) + "-" + start_obj.strftime('%m') + "-" \
        + start_obj.strftime('%d') + " 00:00:00'"
        end_date = str(end_obj.year) + "-" + end_obj.strftime('%m') + "-" \
        + end_obj.strftime('%d') + " 00:00:00'"
    else:
        error_statement = "Start and/or end date string have not been inputted\
        as parseable datetime strings. Please input in format such as \
        'YYYY-MM-DD'"
        return error_statement
    query = base_query + where_query + " timestable between '" + start_date + \
    " and '" + end_date
    #generating pandas frame from db
    generation_window = sql_reader(query)
    #selecting data from specified state or zone
    states = ["NSW", "QLD", "VIC", "TAS", "SA"]
    if region in states:
        state_cond = state_condition()
        generation_window['ntndp_zone_id'] = generation_window['ntndp_zone_id'].map(state_cond)
        generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
    elif type(region) is int and region < 16:
        generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
    elif region is NOARG:
        pass
    else:
        error_statement = "Region has not been inputted correctly or time \
        period has not been inputted. Region must be a string containing one \
        of the eastern states or an integer between 1 and 16. A day offset \
        must be inputted"
        return error_statement
    #cleaning up data to remove useless values, merge data and remove zeroes
    generation_window = generation_window.drop("ntndp_zone_id", axis=1)
    generation_window = generation_window.groupby(["timestable","technology_type_id"]).sum()
    generation_window = generation_window.loc[(generation_window>0).any(1)]
    return generation_window

def plot_gen_window(generation_window):
    """ Makes plot of generation for the given date window."""
    #reordering data for input to plot.area
    generation_window = generation_window.pivot_table(index='timestable', columns='technology_type_id')
    generation_window = generation_window.fillna(0)
    generation_window.columns = generation_window.columns.droplevel()
    generation_window.index = pd.to_datetime(generation_window.index)
    tech_id = tech_legend(generation_window)
    fontP = FontProperties() #small font to fit legend
    fontP.set_size('small')
    generation_window.plot.area()
    sub_ax = plt.subplot(111)
    plt.xlabel('Time')
    plt.ylabel('Generation (MW)')
    #putting legend outside plot area
    sub_ax.legend(labels=tech_id, bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=fontP)
    plt.gcf().subplots_adjust(right=0.7)
    plt.savefig('Generation_Over_Period.png', quality=80)

#running each of the functions and generating the plots
YRS = [2020,2025,2030,2035, 2040]
NO_ST = get_cap_tech_data(YRS)
BAR_FR = plot_cap_by_tech(NO_ST, YRS)
GEN_WIN = get_cap_time_data('12/12/2020', 12, 'SA')
plot_gen_window(GEN_WIN)
