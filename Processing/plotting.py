from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
import pandas as pd
from Processing.loader import DateInput
from Processing.const import PALETTE_2, DISPLAY_ORDER, TECH_NAMES, REGIONS
from json_sqlite import CONFIG

#ignoring mpl deprecation warning
import warnings
warnings.filterwarnings('ignore')

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

class OutputsPlotter():
    """ Makes generation and capacity plots for model outputs."""
    def __init__(self):
        self.handles = []
        self.tech_id = []
        self.tech_color = []

    def tech_legend(self, frame):
        """ Takes tech id's included in df and generates list of those used to be\
        included in plot legend."""
        used_tech = frame.columns.values
        ordered_tech = [x for x in DISPLAY_ORDER if x in used_tech]
        tech_id = [None]*len(used_tech)
        tech_color = [None]*len(used_tech)
        for j, tech_index in enumerate(used_tech):
            tech_color[j] = PALETTE_2[tech_index]
            tech_id[j] = TECH_NAMES[tech_index]
        handles = [None]*len(ordered_tech)
        ordered_tech.reverse()
        for j, tech in enumerate(ordered_tech):
            handles[j] = mpatches.Patch(color=PALETTE_2[tech], label=TECH_NAMES[tech])
        self.handles = handles
        self.tech_id = tech_id
        self.tech_color = tech_color

    def plot_yearly_cap(self, data_class, region=None):
        """ Makes a stacked bar plot of the yearly capacity by technology
            data_class is an Sql_File object."""
        cap = data_class.data['cap'][data_class.data['cap']['value'] > 0]
        if region in REGIONS:
            state_cond = state_condition()
            cap['ntndp_zone_id'] = cap['ntndp_zone_id'].map(state_cond)
            cap = cap.loc[cap['ntndp_zone_id'] == region]
        elif isinstance(region, int) and region <= 16:
            cap = cap.loc[cap['ntndp_zone_id'] == region]
        elif region is None:
            pass
        else:
            print("Region has not been inputted correctly or time period has \
            not been inputted. Region must be a string containing one of the \
            eastern states or an integer between 1 and 16 to specifiy the \
            ntndp_zone_id. A day offset must be inputted")
        cap['value'] = cap['value'].apply(lambda x: x/(10**3)) #conversion to GW
        cap = cap.drop(['ntndp_zone_id', 'name'], axis=1)
        cap = cap.groupby(['technology_type_id', 'year'], as_index=False).sum()
        cap = cap.pivot_table(index='year', columns='technology_type_id', values='value')
        reindexer = [x for x in DISPLAY_ORDER if x in list(cap.columns)]
        cap = cap.reindex(reindexer, axis=1)
        gen = data_class.data['gen']
        gen = gen[gen['value'] > 0]
        if region in REGIONS:
            gen['ntndp_zone_id'] = gen['ntndp_zone_id'].map(state_cond)
            gen = gen.loc[gen['ntndp_zone_id'] == region]
        elif isinstance(region, int) and region <= 16:
            gen = gen.loc[gen['ntndp_zone_id'] == region]
        else:
            gen = gen.drop(['ntndp_zone_id'], axis=1)
        gen = gen.groupby(['year', 'technology_type_id'], as_index=False).sum()
        gen['value'] = gen['value'].apply(lambda x: x/(10**6)) #conversion to TWh
        gen = gen.pivot_table(index='year',
                              columns='technology_type_id',
                              values='value')
        reindexer = [x for x in DISPLAY_ORDER if x in list(gen.columns)]
        gen = gen.reindex(reindexer, axis=1)
        self.tech_legend(cap)
        _, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        cap.plot(ax=ax1, kind='bar', stacked=True, color=self.tech_color)
        ax1.set_ylabel('Capacity (GW)')
        ax1.set_xlabel('')
        ax1.get_legend().remove()
        ax1.set_title('Yearly Capacity')
        self.tech_legend(gen)
        gen.plot(ax=ax2, kind='bar', stacked=True, color=self.tech_color)
        ax2.set_ylabel('Generation (TWh)')
        ax2.set_xlabel('')
        ax2.get_legend().remove()
        ax2.set_title('Yearly Generation')
        plt.gcf().subplots_adjust(right=0.8)
        ax2.legend(handles=self.handles,
                   loc='upper right',
                   bbox_to_anchor=(1.4, 1),
                   fancybox=False,
                   shadow=False)
        fname = CONFIG['local']['json_path'] + \
            '\\Plots\\Yearly_Capacity_' + \
            CONFIG['local']['json_name'][:-5] + \
            '.png'
        plt.savefig(fname, quality=80)

    def plot_generation_slice(self, data_class, start_date, time_period, region=None):
        """ Makes area plot of generation for a time slice specified as a \
        start data and day offset."""
        slice_dates = DateInput(start_date, start_date)
        month = slice_dates.start_obj.month
        day = slice_dates.start_obj.day
        if month == 12 and time_period > (31 - day):
            time_period = 31 - day
        else:
            pass
        slice_dates.end_obj += timedelta(days=time_period)
        slice_dates.end = slice_dates.end_obj.strftime("%Y-%m-%d %H:%M:%S")
        gen = data_class.data['gen']
        generation_window = gen[
            (gen['timestable'] >= slice_dates.start)
            & (gen['timestable'] < slice_dates.end)]
        if region in REGIONS:
            state_cond = state_condition()
            generation_window['ntndp_zone_id'] = generation_window['ntndp_zone_id'].map(state_cond)
            generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
        elif isinstance(region, int) and region <= 16:
            generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
        elif region is None:
            pass
        else:
            print("Region has not been inputted correctly or time period has \
            not been inputted. Region must be a string containing one of the \
            eastern states or an integer between 1 and 16. A day offset must \
            be inputted")
        #cleaning up data to remove useless values, merge data and remove zeroes
        generation_window = generation_window.drop(["ntndp_zone_id", "year"], axis=1)
        generation_window = generation_window.groupby(
            ["timestable", "technology_type_id"], as_index=False).sum()
        generation_window = generation_window.loc[generation_window['value'] > 0]
        generation_window = generation_window.pivot_table(index='timestable',
                                                          columns='technology_type_id',
                                                          values='value')
        reindexer = list(generation_window.columns)
        reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
        generation_window = generation_window.reindex(reindexer, axis=1)
        generation_window = generation_window.fillna(0)
        generation_window.index = pd.to_datetime(generation_window.index)
        self.tech_legend(generation_window)
        font_prop = FontProperties() #small font to fit legend
        font_prop.set_size('small')
        generation_window.plot.area(color=self.tech_color, figsize=[15, 4.8])
        sub_ax = plt.subplot(111)
        plt.ylabel('Generation (MW)')
        plt.xlabel('Timestamp')
        #putting legend outside plot area
        sub_ax.legend(handles=self.handles,
                      bbox_to_anchor=(1.02, 1),
                      ncol=1, fancybox=True,
                      shadow=True,
                      prop=font_prop)
        plt.gcf().subplots_adjust(right=0.85) #0.7 works
        fname = CONFIG['local']['json_path'] + \
                '\\Plots\\Generation_Over_Period_' + \
                CONFIG['local']['json_name'][:-5] + \
                '.png'
        plt.savefig(fname, quality=80)
