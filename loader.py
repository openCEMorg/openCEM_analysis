import os
import math
import json
import imageio
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from os import path
from datetime import timedelta
from func import zone_to_region
from dateutil.parser import parse
from matplotlib.font_manager import FontProperties
from const import *


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
        self.start_obj = parse(start_date)
        self.start = self.start_obj.strftime("%Y-%m-%d %H:%M:%S")
        self.end_obj = parse(end_date)
        self.end = self.end_obj.strftime("%Y-%m-%d %H:%M:%S")

class Sql_File():
    def __init__(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = list(cursor.fetchall())
        names = [i[0] for i in names]
        self.tables = names
        with open(META_NAME, 'r') as _file:
            self.meta = json.load(_file)
        self.yrs = self.meta['Years']

    def get_trans(self):
        if 'interconnector' in self.tables:
            conn = sqlite3.connect(DB_NAME)
            query = "select * from interconnector"
            self.trans = pd.read_sql_query(query, conn)
        else:
            self.trans = None
    def get_gen(self):
        if 'generation' in self.tables:
            conn = sqlite3.connect(DB_NAME)
            #selecting distict to account for duplicate values
            query = "select distinct * from generation"
            self.gen = pd.read_sql_query(query, conn)
            #patch fix to solve double counting
            #self.gen['value'] = self.gen['value'].apply(lambda x: x/2)
        else:
            self.gen = None
    def get_stor(self):
        if 'scheduled_load' in self.tables:
            conn = sqlite3.connect(DB_NAME)
            query = "select * from scheduled_load"
            self.stor = pd.read_sql_query(query, conn)
            self.stor = self.stor[self.stor['name']=='stor_charge']
        else:
            self.stor = None
    def get_cap(self):
        if 'existing_capacity' in self.tables and 'new_capacity' in self.tables:
            conn = sqlite3.connect(DB_NAME)
            query = "select * from existing_capacity"
            self.cap = pd.read_sql_query(query, conn)
        else:
            self.cap = None
    def load_all_data(self):
        self.get_cap()
        self.get_stor()
        self.get_gen()
        self.get_trans()
    def analyse_trans(self):
        trans = self.trans
        trans = trans.drop(['name', 'timestamp'], axis=1)
        map_dict = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
        trans['region_id'] = trans['region_id'].map(map_dict)
        trans['technology_type_id'] = trans['technology_type_id'].map(map_dict)
        trans['value'] = trans['value']/10**3
        trans = trans.pivot_table(
            values='value',
            index = ['region_id', 'technology_type_id'],
            columns = 'year',  aggfunc = np.sum
        )
        trans.index.names = ['  Exported <br> From  ', '  Imported <br> To  ']
        trans.columns.names = ['Simulated <br> Years']
        self.trade = trans
    def analyse_margin(self):
        min_mrg = [None]*len(self.yrs)
        mean_mrg = [None]*len(self.yrs)
        min_t = [None]*len(self.yrs)
        for i, year in enumerate(self.yrs):
            gen = self.gen[self.gen['year'] == year]
            gen = gen.groupby(['timestable'], as_index=False).sum()
            cap = self.cap[self.cap['year'] == year]
            total_cap = cap['value'].sum()
            rsv_mrg = gen
            rsv_mrg['value'] = rsv_mrg['value'].apply(lambda x: 1-x/total_cap)
            min_mrg[i] = min(rsv_mrg['value'])
            mean_mrg[i] = rsv_mrg['value'].mean()
            min_t[i] = rsv_mrg.loc[rsv_mrg['value'].idxmin]['timestable']
        rsv_info = {'min_t': min_t, 'min_marg': min_mrg, 'MARG_MEAN': mean_mrg}
        rsv_info = pd.DataFrame(data=rsv_info)
        self.reserve = rsv_info

    def analyse_meta(self):
        dict_meta = {}
        list_meta = {}
        simple_meta = {}
        for key, value in self.meta.items():
            if isinstance(value, dict):
                dict_meta[key] = value
            elif isinstance(value, list):
                list_meta[key] = value
            elif value is None:
                pass
            else:
                simple_meta[key] = value
        list_meta = pd.DataFrame.from_dict(list_meta)
        if type(self.yrs) is list:
            list_meta.set_index('Years')
            list_meta.index.name = ''
        else:
            pass
        self.dict_meta = dict_meta
        self.list_meta = list_meta
        self.simple_meta = simple_meta

class outputs_plotter():
    def tech_legend(self, frame):
        """ Takes tech id's included in df and generates list of those used to be\
        included in plot legend."""
        used_tech = frame.columns.values
        ordered_tech = [x for x in DISPLAY_ORDER if x in used_tech]
        tech_id = [None]*len(used_tech)
        tech_color = [None]*len(used_tech)
        for j, tech_index in enumerate(used_tech):
            tech_color[j] = PALETTE[tech_index]
            tech_id[j] = TECH_NAMES[tech_index]
        handles = [None]*len(ordered_tech)
        ordered_tech.reverse()
        for j, tech in enumerate(ordered_tech):
            handles[j] = mpatches.Patch(color=PALETTE[tech], label=TECH_NAMES[tech])
        self.handles = handles
        self.tech_id = tech_id
        self.tech_color = tech_color

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

    def plot_yearly_cap(self, data_class, region=None):
        cap = data_class.cap
        cap = cap[cap['value'] > 0]
        cap['value'] = cap['value'].apply(lambda x: x/(10**3)) #conversion to GW
        cap = cap.drop(['ntndp_zone_id','name'], axis=1)
        cap = cap.groupby(['technology_type_id', 'year'], as_index=False).sum()
        cap = cap.pivot_table(index='year', columns='technology_type_id', values='value')
        reindexer = list(cap.columns)
        reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
        cap = cap.reindex(reindexer, axis=1)
        gen = data_class.gen.groupby(['year', 'technology_type_id'], as_index=False).sum()
        gen = gen[gen['value'] > 0]
        gen['value'] = gen['value'].apply(lambda x: x/(10**6)) #conversion to TWh
        gen = gen.drop(['ntndp_zone_id'], axis=1)
        gen = gen.pivot_table(index='year', columns='technology_type_id', values='value')
        reindexer = list(gen.columns)
        reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
        gen = gen.reindex(reindexer, axis=1)
        self.tech_legend(cap)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        cap.plot(ax = ax1, kind='bar', stacked=True, color=self.tech_color)
        ax1.set_ylabel('Capacity (GW)')
        ax1.set_xlabel('')
        ax1.get_legend().remove()
        ax1.set_title('Yearly Capacity')
        gen.plot(ax = ax2, kind='bar', stacked=True, color=self.tech_color)
        ax2.set_ylabel('Generation (TWh)')
        ax2.set_xlabel('')
        ax2.get_legend().remove()
        ax2.set_title('Yearly Generation')
        #sub_ax = plt.subplot(111)
        #box = sub_ax.get_position()
        #resizing figure area to fit the legend
        #sub_ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])
        #sub_ax.set_xticklabels([str(i) for i in data_class.yrs])
        #making the legend
        #sub_ax.legend(labels=self.tech_id, loc='best', bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=font_p)
        #adjusting box size so legend and xlabel aren't cut out
        plt.gcf().subplots_adjust(right=0.8)
        ax2.legend(handles=self.handles, loc='upper right', bbox_to_anchor=(1.4, 1), fancybox=False, shadow=False)
        plt.savefig('Yearly_Capacity.png', quality=80)

    def plot_generation_slice(self, data_class, start_date, time_period, region=None):
        slice_dates = Date_Input(start_date, start_date)
        month = slice_dates.start_obj.month
        day = slice_dates.start_obj.day
        if month == 12 and time_period > (31 - day):
            time_period = 31 - day
        else:
            pass
        slice_dates.end_obj += timedelta(days=time_period)
        slice_dates.end = slice_dates.end_obj.strftime("%Y-%m-%d %H:%M:%S")
        generation_window = data_class.gen[(data_class.gen['timestable'] >= slice_dates.start) & (data_class.gen['timestable'] < slice_dates.end)]
        if region in REGIONS:
            state_cond = state_condition()
            generation_window['ntndp_zone_id'] = generation_window['ntndp_zone_id'].map(state_cond)
            generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
        elif isinstance(region, int) and region <= 16:
            generation_window = generation_window.loc[generation_window['ntndp_zone_id'] == region]
        elif region is None:
            pass
        else:
            error_statement = "Region has not been inputted correctly or time \
            period has not been inputted. Region must be a string containing one \
            of the eastern states or an integer between 1 and 16. A day offset \
            must be inputted"
            print(error_statement)
        #cleaning up data to remove useless values, merge data and remove zeroes
        generation_window = generation_window.drop(["ntndp_zone_id", "year"], axis=1)
        generation_window = generation_window.groupby(["timestable", "technology_type_id"], as_index=False).sum()
        generation_window = generation_window.loc[generation_window['value'] > 0]
        generation_window = generation_window.pivot_table(index='timestable', columns='technology_type_id', values='value')
        reindexer = list(generation_window.columns)
        reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
        generation_window = generation_window.reindex(reindexer, axis=1)
        generation_window = generation_window.fillna(0)
        generation_window.index = pd.to_datetime(generation_window.index)
        self.tech_legend(generation_window)
        fontP = FontProperties() #small font to fit legend
        fontP.set_size('small')
        generation_window.plot.area(color=self.tech_color, figsize=[15, 4.8])
        sub_ax = plt.subplot(111)
        plt.ylabel('Generation (MW)')
        #putting legend outside plot area
        sub_ax.legend(handles=self.handles, bbox_to_anchor=(1.02, 1), ncol=1, fancybox=True, shadow=True, prop=fontP)
        plt.gcf().subplots_adjust(right=0.85) #0.7 works
        plt.savefig('Generation_Over_Period.png', quality=80)

class outputs_animator():
    def __init__(self):
        self.data = Sql_File()
        self.data.get_gen()
        self.data.get_stor()
        self.data.get_trans()

    def clean_data(self, start_date, end_date):
        self.dates = Date_Input(start_date, end_date)

        gen = self.data.gen.loc[(self.data.gen['timestable'] == self.dates.start)]
        gen = gen.rename(columns={'timestable':'timestamp'})
        gen = gen.drop(['year'], axis=1)
        gen = zone_to_region(gen)
        gen_no_tech = gen.groupby(["state"], as_index=False).sum()
        gen = gen.groupby(["state", "technology_type_id"], as_index=False).sum()
        gen_no_tech = gen_no_tech.drop("technology_type_id", axis=1)
        gen_mean = gen.groupby('state').sum()['value'].mean()

        stor = self.data.stor.loc[(self.data.stor['timestamp'] == self.dates.start)]
        stor = stor.drop(['year'], axis=1)
        stor = zone_to_region(stor)
        stor_no_tech = stor.groupby(["state"], as_index=False).sum()
        stor = stor.groupby(["state", "technology_type_id"], as_index=False).sum()
        stor_no_tech = stor_no_tech.drop("technology_type_id", axis=1)

        trans = self.data.trans.loc[(self.data.trans['timestamp'] == self.dates.start)]
        cond = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
        trans["region_id"] = trans["region_id"].map(cond)
        trans["technology_type_id"] = trans["technology_type_id"].map(cond)
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

        load = imports
        load['value'] = gen_no_tech['value']+imports['value']-exports['value']-stor_no_tech['value']

        region_scaler = [None]*len(REGIONS)
        for num, region in enumerate(REGIONS):
            region_scaler[num] = gen.loc[gen['state'] == region].sum().value
        region_scaler = [0.14*round((x**(1/4))/(max(region_scaler)**(1/4)),2) for x in region_scaler]
        region_positions = [[0.65, 0.45], [0.64, 0.63], [0.48, 0.48], [0.58, 0.16], [0.6, 0.3]]
        pie_data = [None]*len(REGIONS)*2
        for num, region in enumerate(REGIONS):
            region_top = gen.loc[gen['state'] == region]
            region_top = region_top.drop("state", axis=1)
            region_top = region_top.set_index("technology_type_id")
            region_top.loc[25] = region_top.sum().value

            reindexer = list(region_top.index)
            reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
            region_top = region_top.reindex(reindexer, axis=0)

            region_bottom = stor.loc[stor['state'] == region]
            region_bottom = region_bottom.drop("state", axis=1)
            region_bottom = region_bottom.set_index("technology_type_id")
            region_bottom.loc[21] = float(load.loc[load['state']==region]['value'])
            region_bottom.loc[25] = region_bottom.sum().value

            reindexer = list(region_bottom.index)
            reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
            region_bottom = region_bottom.reindex(reindexer, axis=0)

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

        self.pie_data = pie_data
        self.link_ratio = link_ratio

    def get_legend(self, start_date, end_date):
        gen_data = self.data.gen[(self.data.gen['timestable'] >= start_date) & (self.data.gen['timestable'] < end_date)]
        gen_data = gen_data.rename(columns={'timestable':'timestamp'})
        stor_data = self.data.stor[(self.data.stor['timestamp'] >= start_date) & (self.data.stor['timestamp'] < end_date)]
        all_data = gen_data.append(stor_data)
        all_data = all_data.drop(['ntndp_zone_id', 'name', 'year'], axis=1)
        all_data = all_data.groupby(['technology_type_id'], as_index=False).sum()
        big_tech = all_data.nlargest(9, ['value'])
        big_tech = big_tech.append([{'technology_type_id': 21, 'value':1}])
        big_tech = list(big_tech['technology_type_id'])
        big_tech = [x for x in DISPLAY_ORDER if x in big_tech]
        big_tech.reverse()
        big_tech.append(big_tech.pop(0))
        handles = [None]*len(big_tech)
        for j, tech in enumerate(big_tech):
            handles[j] = mpatches.Patch(color=PALETTE[tech], label=TECH_W_LOAD[tech])
        self.handles = handles

    def map_plotter(self):
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
        techs = list(self.pie_data[0][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = techs
        values = list(self.pie_data[0][0]['value'])
        ax_pie = fig.add_axes([0.6-self.pie_data[0][2]/2, 0.37-self.pie_data[0][2]/2, self.pie_data[0][2], self.pie_data[0][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[0][5], radius=self.pie_data[0][1], colors=smallpalette)
        patch_counter = len(self.pie_data[0][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[1][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[1][0]['value'])
        ax_pie = fig.add_axes([0.6-self.pie_data[1][2]/2, 0.37-self.pie_data[1][2]/2, self.pie_data[1][2], self.pie_data[1][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[1][5], radius=self.pie_data[1][1], colors=smallpalette)
        patch_counter = patch_counter+len(self.pie_data[1][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # -- QLD ==
        # top pie
        techs = list(self.pie_data[2][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[2][0]['value'])
        ax_pie = fig.add_axes([0.59-self.pie_data[2][2]/2, 0.55-self.pie_data[2][2]/2, self.pie_data[2][2], self.pie_data[2][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[2][5], radius=self.pie_data[2][1], colors=smallpalette)
        patch_counter = len(self.pie_data[2][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[3][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[3][0]['value'])
        ax_pie = fig.add_axes([0.59-self.pie_data[3][2]/2, 0.55-self.pie_data[3][2]/2, self.pie_data[3][2], self.pie_data[3][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[3][5], radius=self.pie_data[3][1], colors=smallpalette)
        patch_counter = patch_counter+len(self.pie_data[3][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # --SA --
        # top pie
        techs = list(self.pie_data[4][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[4][0]['value'])
        ax_pie = fig.add_axes([0.43-self.pie_data[4][2]/2, 0.43-self.pie_data[4][2]/2, self.pie_data[4][2], self.pie_data[4][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[4][5], radius=self.pie_data[4][1], colors=smallpalette)
        patch_counter = len(self.pie_data[4][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[5][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[5][0]['value'])
        ax_pie = fig.add_axes([0.43-self.pie_data[5][2]/2, 0.43-self.pie_data[5][2]/2, self.pie_data[5][2], self.pie_data[5][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[5][5], radius=self.pie_data[5][1], colors=smallpalette)
        patch_counter = patch_counter+len(self.pie_data[5][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # -- TAS ==
        # top pie
        techs = list(self.pie_data[6][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[6][0]['value'])
        ax_pie = fig.add_axes([0.57-self.pie_data[6][2]/2, 0.13-self.pie_data[6][2]/2, self.pie_data[6][2], self.pie_data[6][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[6][5], radius=self.pie_data[6][1], colors=smallpalette)
        patch_counter = len(self.pie_data[6][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[7][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[7][0]['value'])
        ax_pie = fig.add_axes([0.57-self.pie_data[7][2]/2, 0.13-self.pie_data[7][2]/2, self.pie_data[7][2], self.pie_data[7][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[7][5], radius=self.pie_data[7][1], colors=smallpalette)
        patch_counter = patch_counter+len(self.pie_data[7][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # -- VIC ==
        # top pie
        techs = list(self.pie_data[8][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[8][0]['value'])
        ax_pie = fig.add_axes([0.55-self.pie_data[8][2]/2, 0.25-self.pie_data[8][2]/2, self.pie_data[8][2], self.pie_data[8][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[8][5], radius=self.pie_data[8][1], colors=smallpalette)
        patch_counter = len(self.pie_data[8][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[9][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech+techs))
        values = list(self.pie_data[9][0]['value'])
        ax_pie = fig.add_axes([0.55-self.pie_data[9][2]/2, 0.25-self.pie_data[9][2]/2, self.pie_data[9][2], self.pie_data[9][2]], zorder=3)
        ax_pie.pie(values, counterclock=self.pie_data[9][5], radius=self.pie_data[9][1], colors=smallpalette)
        patch_counter = patch_counter+len(self.pie_data[9][0])
        ax_pie.patches[patch_counter-1].set_alpha(0)
        #defining arrow end locations
        arr_start = [[510, 695], #NSW to VIC
                    [455, 535], #NSW to QLD
                    [225, 602], #SA to VIC
                    [395, 843],]  #TAS to VIC
        arr_disp = [[-45, 60],
                    [0, -40],
                    [80, 115],
                    [5, 14]]
        line_ends = [[[510, 460], [690, 780]], #NSW_VIC
                    [[450, 450], [540, 480]], #NSW_QLD
                    [[225, 300], [595, 725]], #SA_VIC
                    [[385, 400], [840, 865]]] #TAS_VIC
        #making arrows for trade
        for i, ratio in enumerate(self.link_ratio):
            if ratio < 0: #if trade in some direction as link is defined
                ax.arrow(arr_start[i][0], arr_start[i][1], arr_disp[i][0], arr_disp[i][1], linewidth=ratio*10, head_length=5, head_width=7, zorder=5)
            elif ratio > 0: #if trade in the other direction
                #adjust the arrow so it goes the right way
                x = arr_start[i][0] + arr_disp[i][0]
                y = arr_start[i][1] + arr_disp[i][1]
                dx = -arr_disp[i][0]
                dy = -arr_disp[i][1]
                ax.arrow(x, y, dx, dy, linewidth=abs(ratio)*10, head_length=5, head_width=7, zorder=5)
            else: # if there is no trade make a real small arrow with no head
                ax.arrow(arr_start[i][0], arr_start[i][1], arr_disp[i][0], arr_disp[i][1], linewidth=0.3, head_length=0.01, head_width=0.01, zorder=5)
                #ax.plot(line_ends[i][0], line_ends[i][1], linewidth=1, color='k', zorder=5)
                pass
        #plotting the pie legend in the top right
        ax_pie_legend = fig.add_axes([0.75, 0.6, 0.15, 0.15], zorder=3)
        ax_pie_legend.pie([1, 1], colors = [(46/255, 49/255, 49/255, 1), (171/255, 183/255, 183/255, 1)])
        ax_pie_legend.set_title('Producers', fontsize = 8)
        ax_pie_legend.set_xlabel('Consumers', fontsize = 8)
        ax_pie_legend.legend(bbox_to_anchor=(-0.25, -0.4), loc=2, borderaxespad=0., handles=self.handles, ncol=1)
        #drawing lines
        pie_positions = [[455, 625], [445, 405], [180, 550], [410, 920], [380, 775]]
        self.fig = fig

    def main(self, start_date, length):
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
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        self.get_legend(start_date_str, end_date_str)
        for single_date in daterange(start_date, end_date):
            date = single_date.strftime("%Y-%m-%d %H:%M")
            print(date)

            self.clean_data(date, date)
            self.map_plotter()

            filename = "frame_" + single_date.strftime("%Y-%m-%d-%H-%M") +".png"
            filenames = filenames + [filename]
            title = 'OpenCEM Simulation Data for ' + str(length) + ' Days From ' + start_date.strftime("%d/%m/%Y")
            self.fig.suptitle(title)
            self.fig.text(0.45, 0.03, single_date.strftime("%Y-%m-%d %H:%M"))
            self.fig.savefig(path.join(save_dir, filename), dpi=200)
            plt.close('all')
        with imageio.get_writer(path.join(save_dir, "animation.gif"), mode='I', fps=3) as writer:
            for filename in filenames:
                image = imageio.imread(path.join(save_dir, filename))
                writer.append_data(image)
