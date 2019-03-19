import os
import math
import imageio
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from os import path
from datetime import timedelta
from dateutil.parser import parse
from IO_functions import sql_reader, is_date
from matplotlib.font_manager import FontProperties



class Date_Input():
    def __init__(self, start_date, end_date):
        if start_date is None and end_date is None:
            start_date = '2020-01-01'
            end_date = '2045-12-31'
        else:
            try:
                parse(start_date)
                try:
                    parse(end_date)
                except (ValueError, TypeError) as e:
                    end_date = start_date
            except (ValueError, TypeError) as e:
                error_statement = "Either two dates have not been inputted as \
                arguments or one of the dates cannot be recognised as a date. \
                Please input two dates in a format such as 'YYYY-MM-DD.'"
                print(error_statement)
        self.start = parse(start_date)
        self.start = self.start.strftime("%Y-%m-%d %H:%M:%S")
        self.end = parse(end_date)
        self.end = self.end.strftime("%Y-%m-%d %H:%M:%S")

class Sql_File():
    def __init__(self):
        self.yrs = [2020, 2025, 2030, 2035, 2040, 2045]
        self.regions = ['NSW', 'QLD', 'SA', 'TAS', 'VIC']
        self.palette = {1: (161 / 255, 135 / 255, 111 / 255, 1),  # biomass
                   2: (251 / 255, 177 / 255, 98 / 255, 1),  # ccgt
                   3: (251 / 255, 177 / 255, 98 / 255, 0.75),  # ccgt_sc
                   4: (25 / 255, 25 / 255, 25 / 255, 1),  # coal_sc
                   5: (25 / 255, 25 / 255, 25 / 255, 0.75),  # coal_sc_scc
                   6: (137 / 255, 87 / 255, 45 / 255, 1),  # brown_coal_sc
                   7: (137 / 255, 87 / 255, 45 / 255, 0.75),   # brown_coal_sc_scc
                   8: (253 / 255, 203 / 255, 148 / 255, 1),  # ocgt
                   9: (220 / 255, 205 / 255, 0, 0.6),  # PV DAT
                   10: (220 / 255, 205 / 255, 0 / 255, 0.8),  # PV fixed
                   11: (220 / 255, 205 / 255, 0 / 255, 1),  # PV SAT
                   12: (67 / 255, 116 / 255, 14 / 255, 1),  # Wind
                   13: (1, 209 / 255, 26 / 255, 1),  # CST 6h
                   14: (137 / 255, 174 / 255, 207 / 255, 1),  # PHES 6 h
                   15: (43 / 255, 161 / 255, 250 / 255, 1),  # Battery
                   16: (240 / 255, 79 / 255, 35 / 255, 1),  # recip engine,
                   17: (128 / 255, 191 / 255, 1, 1),  # Wind high
                   18: (75 / 255, 130 / 255, 178 / 255, 1),  # Hydro
                   19: (241 / 255, 140 / 255, 31 / 255, 1),  # Gas thermal
                   20: (0 / 255, 96 / 255, 1, 1),  # pumps
                   21: (243 / 255, 80 / 255, 32 / 255, 1),  # load (uses OpenNEM distillate colour)
                   22: (140 / 255, 140 / 255, 140 / 255, 1),  # Light gray other tech 1
                   23: (145 / 255, 145 / 255, 145 / 255, 1),  # Light gray other tech 2
                   24: (150 / 255, 150 / 255, 150 / 255, 1),  # Light gray other tech 3
                   25: (160 / 255, 160 / 255, 160 / 255, 1),  # Light gray other tech 4
                   }
    def get_trans(self):
        conn = sqlite3.connect("test.db")
        query = "select * from interconnector"
        self.trans = pd.read_sql_query(query, conn)
    def get_gen(self):
        conn = sqlite3.connect("test.db")
        query = "select * from generation"
        self.gen = pd.read_sql_query(query, conn)
    def get_stor(self):
        conn = sqlite3.connect("test.db")
        query = "select * from scheduled_load"
        self.stor = pd.read_sql_query(query, conn)
    def get_cap(self):
        conn = sqlite3.connect("test.db")
        query = "select * from existing_capacity"
        self.cap = pd.read_sql_query(query, conn)
    def load_all_data(self):
        self.get_cap()
        self.get_stor()
        self.get_gen()
        self.get_trans()
    def analyse_trans(self):
        trans = self.trans
        trans = trans.groupby(['region_id', 'technology_type_id'], as_index=False).sum()
        trans = trans.pivot_table(index='region_id', columns='technology_type_id')
        trans = trans.fillna('')
        trans.columns = trans.columns.droplevel()
        trans.columns = [self.regions[k-1] for k in trans.columns]
        trans.index = [self.regions[k-1] for k in trans.index]
        trans.columns.name = 'Transmission To'
        trans.index.name = 'Transmission From'
        self.trade = trans
    def make_yearly_plot(self, date, period, region=None):
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
            """ Takes tech id's included in df and generates list of those used to be\
            included in plot legend."""
            tech_names = ['Biomass', 'CCGT', 'CCGT CCS', 'Coal SC', 'Coal SC CCS', \
            'Brown Coal SC', 'Brown Coal SC CCS', 'OCGT', 'Solar PV DAT', 'Solar PV FFP',\
            'Solar PV SAT', 'Wind', 'CST 6h', 'PHES 6h', 'Battery 2h', 'Recip Engine',\
            'Wind H', 'Hydro', 'Gas (Thermal)', 'Pumps']
            used_tech = frame.columns.values
            tech_id = [None]*len(used_tech)
            tech_color = [None]*len(used_tech)
            for j, tech_index in enumerate(used_tech):
                tech_color[j] = self.palette[tech_index]
                tech_id[j] = tech_names[tech_index-1]
            return tech_id, tech_color
        def get_cap_tech_data(sel_years):
            """ Loads capacity data into pandas frame based on given years."""
            yrs = [2020, 2025, 2030, 2035, 2040, 2045] #modelled years
            #loads capacity data into frame
            mod_years = len(yrs)
            no_sel_yr = len(sel_years)
            no_cap_yr = int(len(self.cap)/mod_years)
            #removes other year data, years aren't specified in the db so data is split
            # and checked against the selected years then removed if not within the range
            new_capacity = [None]*no_sel_yr
            no_state = [None]*no_sel_yr
            j = 0
            for i in range(0, no_sel_yr):
                if yrs[i] not in sel_years:
                    self.cap = self.cap.iloc[no_cap_yr:]
                else:
                    new_capacity[j] = self.cap.iloc[0:no_cap_yr]
                    self.cap = self.cap.iloc[no_cap_yr:]
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
            bar_frame = bar_frame.divide(1000) #converting MW to GW
            #making stacked bar plot
            tech_id, tech_color = tech_legend(bar_frame)
            font_p = FontProperties()
            font_p.set_size('small') #smaller font because the legend is large
            bar_frame.plot(kind='bar', stacked=True, color=tech_color)
            plt.ylabel('Capacity(GW)')
            sub_ax = plt.subplot(111)
            box = sub_ax.get_position()
            #resizing figure area to fit the legend
            sub_ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])
            sub_ax.set_xticklabels([str(i) for i in years])
            #making the legend
            sub_ax.legend(labels=tech_id, loc='best', bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=font_p)
            #adjusting box size so legend and xlabel aren't cut out
            plt.gcf().subplots_adjust(bottom=0.25)
            plt.gcf().subplots_adjust(right=0.7)
            plt.savefig('Yearly_Capacity.png', quality=80)
        def get_cap_time_data(start_date, time_period, region=None):
            """Gets time slice generation data to be plotted. Time period must be \
            specified. """
            generation_window = self.gen
            #reading in data input
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
            #selecting data between specified dates
            generation_window = generation_window.loc[(generation_window['timestable'] >= start_date) & (generation_window['timestable'] < end_date)]
            #selecting data from specified state or zone
            states = ["NSW", "QLD", "VIC", "TAS", "SA"]
            if region in states:
                state_cond = state_condition()
                generation_window['ntndp_zone_id'] = generation_window['ntndp_zone_id'].map(state_cond)
                generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
            elif isinstance(region, int) and region < 16:
                generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
            elif region is None:
                pass
            else:
                error_statement = "Region has not been inputted correctly or time \
                period has not been inputted. Region must be a string containing one \
                of the eastern states or an integer between 1 and 16. A day offset \
                must be inputted"
                return error_statement
            #cleaning up data to remove useless values, merge data and remove zeroes
            generation_window = generation_window.drop("ntndp_zone_id", axis=1)
            generation_window = generation_window.groupby(["timestable", "technology_type_id"]).sum()
            generation_window = generation_window.loc[(generation_window > 0).any(1)]
            return generation_window
        def plot_gen_window(generation_window):
            """ Makes plot of generation for the given date window."""
            #reordering data for input to plot.area
            generation_window = generation_window.pivot_table(index='timestable', columns='technology_type_id')
            generation_window = generation_window.fillna(0)
            generation_window.columns = generation_window.columns.droplevel()
            generation_window.index = pd.to_datetime(generation_window.index)
            tech_id, tech_color = tech_legend(generation_window)
            fontP = FontProperties() #small font to fit legend
            fontP.set_size('small')
            generation_window.plot.area(color=tech_color)
            sub_ax = plt.subplot(111)
            plt.ylabel('Generation (MW)')
            #putting legend outside plot area
            sub_ax.legend(labels=tech_id, bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=fontP)
            plt.gcf().subplots_adjust(right=0.7)
            plt.savefig('Generation_Over_Period.png', quality=80)
        no_st = get_cap_tech_data(self.yrs)
        plot_cap_by_tech(no_st, self.yrs)
        gen_win = get_cap_time_data(date, period, region)
        plot_gen_window(gen_win)
    def animate(self, start_date, length):
        def zone_to_region(frame):
            if frame.columns.values[0] == 'ntndp_zone_id':
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
                frame["ntndp_zone_id"] = frame["ntndp_zone_id"].map(state_cond)
                frame = frame.groupby(['ntndp_zone_id', 'technology_type_id', 'timestamp'], as_index=False).sum()
                frame = frame.rename(columns={'ntndp_zone_id':'state'})
            else:
                pass
            return frame
        def get_data(start_date=None, end_date=None):
            #getting date info
            dates = Date_Input(start_date, end_date)
            #generation data
            self.get_gen()
            gen = self.gen.loc[(self.gen['timestable'] == dates.start)]
            self.gen = None
            gen = gen.rename(columns={'timestable':'timestamp'})
            gen = zone_to_region(gen)
            print("got gen")
            #storage data
            self.get_stor()
            stor = self.stor.loc[(self.stor['timestamp'] == dates.start)]
            self.stor = None
            print("got stor")
            stor = zone_to_region(stor)
            #transmission data
            self.get_trans()
            trans = self.trans.loc[(self.trans['timestamp'] == dates.start)]
            self.trans = None
            print("got trans")
            cond = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
            trans["region_id"] = trans["region_id"].map(cond)
            trans["technology_type_id"] = trans["technology_type_id"].map(cond)
            #manipulating transmission data
            exports = trans.groupby(['region_id'], as_index=False).sum()
            imports = trans.groupby(['technology_type_id'], as_index=False).sum()
            imports = imports.rename(columns={'technology_type_id':'state'})
            exports = exports.rename(columns={'region_id':'state'})
            trans = trans.groupby(["region_id", "technology_type_id"], as_index=False).sum()
            links = [('NSW', 'VIC'), ('NSW', 'QLD'), ('VIC', 'SA'), ('VIC', 'TAS')]
            link_trade = pd.Series([0]*len(links), index=links)
            for i, value in enumerate(trans.value):
                region_from = trans['region_id'][i]
                region_to = trans['technology_type_id'][i]
                for j, link in enumerate(link_trade.index):
                    if region_to in link and region_from in link:
                        if region_from == link[1]:
                            link_trade[j] = link_trade[j] + value
                        else:
                            link_trade[j] = link_trade[j] - value
                    else:
                        pass
            link_ratio = [None]*len(links)
            for i, val in enumerate(link_trade):
                link_ratio[i] = abs(val)**(1.0/3)/20000**(1.0/3)
            return gen, stor, imports, exports, link_ratio
        def main(start_date=None, end_date=None):
            pie_data = [None]*len(self.regions)*2
            gen, stor, imports, exports, link_ratio = get_data(start_date, end_date)
            gen_no_tech = gen.groupby(["state"], as_index=False).sum()
            gen = gen.groupby(["state", "technology_type_id"], as_index=False).sum()
            stor_no_tech = stor.groupby(["state"], as_index=False).sum()
            stor = stor.groupby(["state", "technology_type_id"], as_index=False).sum()
            gen_no_tech = gen_no_tech.drop("technology_type_id", axis=1)
            stor_no_tech = stor_no_tech.drop("technology_type_id", axis=1)
            load = imports
            load['value'] = gen_no_tech['value']+imports['value']-exports['value']-stor_no_tech['value']
            gen_mean = gen.groupby('state').sum()['value'].mean()
            region_scaler = [None]*len(self.regions)
            for num, region in enumerate(self.regions):
                region_scaler[num] = gen.loc[gen['state'] == region].sum().value
            region_scaler = [0.14*round((x**(1/4))/(max(region_scaler)**(1/4)),2) for x in region_scaler]
            region_positions = [[0.65, 0.45], [0.64, 0.63], [0.48, 0.48], [0.58, 0.16], [0.6, 0.3]]

            for num, region in enumerate(self.regions):
                region_top = gen.loc[gen['state'] == region]
                region_top = region_top.drop("state", axis=1)
                region_top = region_top.set_index("technology_type_id")
                region_top.loc[25] = region_top.sum().value
                region_bottom = stor.loc[stor['state'] == region]
                region_bottom = region_bottom.drop("state", axis=1)
                region_bottom = region_bottom.set_index("technology_type_id")
                region_bottom.loc[21] = float(load.loc[load['state']==region]['value'])
                region_bottom.loc[25] = region_bottom.sum().value
                region_ratio = gen[gen['state']==region].sum().value
                region_top = region_top.loc[(region_top!=0).any(axis=1)]
                region_bottom = region_bottom.loc[(region_bottom!=0).any(axis=1)]
                gen_load_ratio = (region_top.sum().value)**(3/2)/(region_bottom.sum().value)**(3/2)
                if gen_load_ratio >= 1:
                    bottom_radius = 1/gen_load_ratio
                    top_radius = 1
                else:
                    bottom_radius = 1
                    top_radius = 1*gen_load_ratio
                pie_data[num*2] = [region_top, top_radius, region_scaler[num], region_positions[num][0], region_positions[num][1], True]
                pie_data[num*2+1] = [region_bottom, bottom_radius, region_scaler[num], region_positions[num][0], region_positions[num][1], False]
            return pie_data, link_ratio

        def get_legend(start_date, end_date, pie_data, link_ratio):
            all_data = pie_data[0][0]
            for i in range(1, len(pie_data)):
                all_data = all_data.append(pie_data[i][0])
            all_data = all_data.reset_index().groupby(['technology_type_id'], as_index=False).sum()
            used_tech = all_data.nlargest(13, ['technology_type_id'])
            used_tech = used_tech[used_tech['technology_type_id']!=25]
            used_tech = list(used_tech['technology_type_id'])
            tech_legend = ['Biomass', 'CCGT', 'CCGT CCS', 'Coal SC', 'Coal SC CCS', \
            'Brown Coal SC', 'Brown Coal SC CCS', 'OCGT', 'Solar PV DAT', 'Solar PV FFP',\
            'Solar PV SAT', 'Wind', 'CST 6h', 'PHES 6h', 'Battery 2h', 'Recip Engine',\
            'Wind H', 'Hydro', 'Gas (Thermal)', 'Pumps', 'Load']
            handles = [None]*len(used_tech)
            for j, tech in enumerate(used_tech):
                handles[j] = mpatches.Patch(color=self.palette[tech], label=tech_legend[tech-1])
            return handles

        def map_plotter(pie_data, link_ratio, handles):
            #first the image is loaded in
            map_img = plt.imread('aust3.png')
            #make the plots
            fig, ax = plt.subplots()
            ax.imshow(map_img, zorder=1)
            plt.axis('off')
            pie_locations = {0: (0.6, 0.37), #NSW
                            1: (0.59, 0.55), #QLD
                            2: (0.43, 0.43), #SA
                            3: (0.57, 0.13), #TAS
                            4: (0.55, 0.25)} #VIC
            # -- NSW --
            # top pie
            techs = list(pie_data[0][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = techs
            ax_pie = fig.add_axes([0.6-pie_data[0][2]/2, 0.37-pie_data[0][2]/2, pie_data[0][2], pie_data[0][2]], zorder=3)
            ax_pie.pie(pie_data[0][0], counterclock=pie_data[0][5], radius=pie_data[0][1], colors=smallpalette)
            patch_counter = len(pie_data[0][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # bottom pie
            techs = list(pie_data[1][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.6-pie_data[1][2]/2, 0.37-pie_data[1][2]/2, pie_data[1][2], pie_data[1][2]], zorder=3)
            ax_pie.pie(pie_data[1][0], counterclock=pie_data[1][5], radius=pie_data[1][1], colors=smallpalette)
            patch_counter = patch_counter+len(pie_data[1][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # -- QLD ==
            # top pie
            techs = list(pie_data[2][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.59-pie_data[2][2]/2, 0.55-pie_data[2][2]/2, pie_data[2][2], pie_data[2][2]], zorder=3)
            ax_pie.pie(pie_data[2][0], counterclock=pie_data[2][5], radius=pie_data[2][1], colors=smallpalette)
            patch_counter = len(pie_data[2][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # bottom pie
            techs = list(pie_data[3][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.59-pie_data[3][2]/2, 0.55-pie_data[3][2]/2, pie_data[3][2], pie_data[3][2]], zorder=3)
            ax_pie.pie(pie_data[3][0], counterclock=pie_data[3][5], radius=pie_data[3][1], colors=smallpalette)
            patch_counter = patch_counter+len(pie_data[3][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # --SA --
            # top pie
            techs = list(pie_data[4][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.43-pie_data[4][2]/2, 0.43-pie_data[4][2]/2, pie_data[4][2], pie_data[4][2]], zorder=3)
            ax_pie.pie(pie_data[4][0], counterclock=pie_data[4][5], radius=pie_data[4][1], colors=smallpalette)
            patch_counter = len(pie_data[4][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # bottom pie
            techs = list(pie_data[5][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.43-pie_data[5][2]/2, 0.43-pie_data[5][2]/2, pie_data[5][2], pie_data[5][2]], zorder=3)
            ax_pie.pie(pie_data[5][0], counterclock=pie_data[5][5], radius=pie_data[5][1], colors=smallpalette)
            patch_counter = patch_counter+len(pie_data[5][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # -- TAS ==
            # top pie
            techs = list(pie_data[6][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.57-pie_data[6][2]/2, 0.13-pie_data[6][2]/2, pie_data[6][2], pie_data[6][2]], zorder=3)
            ax_pie.pie(pie_data[6][0], counterclock=pie_data[6][5], radius=pie_data[6][1], colors=smallpalette)
            patch_counter = len(pie_data[6][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # bottom pie
            techs = list(pie_data[7][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.57-pie_data[7][2]/2, 0.13-pie_data[7][2]/2, pie_data[7][2], pie_data[7][2]], zorder=3)
            ax_pie.pie(pie_data[7][0], counterclock=pie_data[7][5], radius=pie_data[7][1], colors=smallpalette)
            patch_counter = patch_counter+len(pie_data[7][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # -- VIC ==
            # top pie
            techs = list(pie_data[8][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.55-pie_data[8][2]/2, 0.25-pie_data[8][2]/2, pie_data[8][2], pie_data[8][2]], zorder=3)
            ax_pie.pie(pie_data[8][0], counterclock=pie_data[8][5], radius=pie_data[8][1], colors=smallpalette)
            patch_counter = len(pie_data[8][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            # bottom pie
            techs = list(pie_data[9][0].index)
            smallpalette = [self.palette[k] for k in techs]
            used_tech = list(set(used_tech+techs))
            ax_pie = fig.add_axes([0.55-pie_data[9][2]/2, 0.25-pie_data[9][2]/2, pie_data[9][2], pie_data[9][2]], zorder=3)
            ax_pie.pie(pie_data[9][0], counterclock=pie_data[9][5], radius=pie_data[9][1], colors=smallpalette)
            patch_counter = patch_counter+len(pie_data[9][0])
            ax_pie.patches[patch_counter-1].set_alpha(0)
            #defining arrow end locations
            arr_start = [[510, 695], #NSW to VIC
                        [455, 535], #NSW to QLD
                        [225, 602], #SA to VIC
                        [400, 857],]  #TAS to VIC
            arr_disp = [[-45, 60],
                        [0, -40],
                        [80, 115],
                        [-5, -14]]
            line_ends = [[[510, 460], [690, 780]], #NSW_VIC
                        [[450, 450], [540, 480]], #NSW_QLD
                        [[225, 300], [595, 725]], #SA_VIC
                        [[385, 400], [840, 865]]] #TAS_VIC
            #making arrows for trade
            for i, ratio in enumerate(link_ratio):
                if ratio < 0:
                    ax.arrow(arr_start[i][0], arr_start[i][1], arr_disp[i][0], arr_disp[i][1], linewidth=ratio*10, head_length=5, head_width=7, zorder=5)
                elif ratio > 0:
                    x = arr_start[i][0] + arr_disp[i][0]
                    y = arr_start[i][1] + arr_disp[i][1]
                    dx = -arr_disp[i][0]
                    dy = -arr_disp[i][1]
                    ax.arrow(x, y, dx, dy, linewidth=abs(ratio)*10, head_length=5, head_width=7, zorder=5)
                else:
                    ax.plot(line_ends[i][0], line_ends[i][1], linewidth=1, color='k', zorder=5)
                    pass
            #plotting the pie legend in the top right
            ax_pie_legend = fig.add_axes([0.75, 0.6, 0.15, 0.15], zorder=3)
            ax_pie_legend.pie([1, 1], colors = [(46/255, 49/255, 49/255, 1), (171/255, 183/255, 183/255, 1)])
            ax_pie_legend.set_title('Producers', fontsize = 8)
            ax_pie_legend.set_xlabel('Consumers', fontsize = 8)
            ax_pie_legend.legend(bbox_to_anchor=(-0.25, -0.4), loc=2, borderaxespad=0., handles=handles, ncol=1)
            #drawing lines
            pie_positions = [[455, 625], [445, 405], [180, 550], [410, 920], [380, 775]]
            return fig

        def make_animation(start_date, length):
            plt.clf()
            ims = []
            filenames = []
            start_date = parse(start_date)
            end_date = start_date + timedelta(days=length)
            save_dir = os.getcwd() + '\\Animation'
            def daterange(start_date, end_date):
                delta = timedelta(hours=1)
                while start_date < end_date:
                    yield start_date
                    start_date += delta
            for single_date in daterange(start_date, end_date):
                date = single_date.strftime("%Y-%m-%d %H:%M")
                print(date)
                pie_data, link_ratio = main(date)
                handles = get_legend(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), pie_data, link_ratio)
                fig = map_plotter(pie_data, link_ratio, handles)
                filename = "frame_" + single_date.strftime("%Y-%m-%d-%H-%M") +".png"
                filenames = filenames + [filename]
                title = 'OpenCEM Simulation Data for ' + str(length) + ' Days From ' + start_date.strftime("%Y-%m-%d")
                fig.suptitle(title)
                fig.text(0.45, 0.03, single_date.strftime("%Y-%m-%d %H:%M"))
                fig.savefig(path.join(save_dir, filename))
                plt.close('all')
            with imageio.get_writer(path.join(save_dir, "animation.gif"), mode='I', fps=3) as writer:
                for filename in filenames:
                    image = imageio.imread(path.join(save_dir, filename))
                    writer.append_data(image)
        make_animation(start_date, length)
