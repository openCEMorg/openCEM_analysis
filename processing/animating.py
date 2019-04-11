'''Module to produce animations'''
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

import glob
import os

import warnings
from datetime import timedelta

import imageio
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from dateutil.parser import parse

from json_sqlite import CONFIG
from processing.const import DISPLAY_ORDER, PALETTE, REGIONS, TECH_W_LOAD
from processing.func import zone_to_region
from processing.loader import DateInput, SqlFile

warnings.filterwarnings('ignore')


class OutputsAnimator():
    """ Makes an animation incorproating technology based pie charts demand \
    for each region plotting consumption and generation overlaid on an \
    Australian map. Interconnector trade also included."""

    def __init__(self):
        """ Loads the required data """
        self.sqldata = SqlFile()
        self.sqldata.get_gen()
        self.sqldata.get_stor()
        self.sqldata.get_trans()
        self.dates = []
        self.pie_data = []
        self.link_ratio = []

    def clean_data(self, start_date, end_date):
        """ Formatting and cleaning of data into easy format for plotting. """
        self.dates = DateInput(start_date, end_date)
        # cleaning generation data
        gen = self.sqldata.data['gen']
        gen = gen.loc[(gen['timestable'] == self.dates.start)]
        gen = gen.rename(columns={'timestable': 'timestamp'})
        gen = gen.drop(['year'], axis=1)
        gen = zone_to_region(gen)
        gen_no_tech = gen.groupby(["state"], as_index=False).sum()
        gen = gen.groupby(["state", "technology_type_id"], as_index=False).sum()
        gen_no_tech = gen_no_tech.drop("technology_type_id", axis=1)
        # cleaning storage data
        stor = self.sqldata.data['stor']
        stor = stor.loc[(stor['timestamp'] == self.dates.start)]
        stor = stor.drop(['year'], axis=1)
        stor = zone_to_region(stor)
        stor_no_tech = stor.groupby(["state"], as_index=False).sum()
        stor = stor.groupby(["state", "technology_type_id"], as_index=False).sum()
        stor_no_tech = stor_no_tech.drop("technology_type_id", axis=1)
        # cleaning transmission data
        trans = self.sqldata.data['trans']
        trans = trans.loc[(trans['timestamp'] == self.dates.start)]
        cond = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
        trans["region_id"] = trans["region_id"].map(cond)
        trans["technology_type_id"] = trans["technology_type_id"].map(cond)
        exports = trans.groupby(['region_id'], as_index=False).sum()
        imports = trans.groupby(['technology_type_id'], as_index=False).sum()
        imports = imports.rename(columns={'technology_type_id': 'state'})
        exports = exports.rename(columns={'region_id': 'state'})
        trans = trans.groupby(["region_id", "technology_type_id"], as_index=False).sum()
        links = [('NSW', 'VIC'), ('NSW', 'QLD'), ('VIC', 'SA'), ('VIC', 'TAS')]
        link_trade = pd.Series([0] * len(links), index=links)
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
        link_ratio = [None] * len(links)
        for i, val in enumerate(link_trade):
            link_ratio[i] = abs(val)**(1.0 / 3) / 20000**(1.0 / 3)

        load = imports
        load['value'] = gen_no_tech['value'] + imports['value'] - \
            exports['value'] - stor_no_tech['value']

        # regions scaled against each other. Scaled using an x^(1/4)/y^(1/4) ratio
        region_scaler = [None] * len(REGIONS)
        for num, region in enumerate(REGIONS):
            region_scaler[num] = gen.loc[gen['state'] == region].sum().value
        region_scaler = [0.14 * round(x**(1 / 4) / max(region_scaler)**(1 / 4), 2)
                         for x in region_scaler]
        region_positions = [[0.65, 0.45], [0.64, 0.63], [0.48, 0.48], [0.58, 0.16], [0.6, 0.3]]
        # formatting data for input to matplotlib methods
        # all data held in a list: pie_data
        pie_data = [None] * len(REGIONS) * 2
        for num, region in enumerate(REGIONS):
            # top pie chart data (generation)
            region_top = gen.loc[gen['state'] == region]
            region_top = region_top.drop("state", axis=1)
            region_top = region_top.set_index("technology_type_id")
            # placeholder value, made transparent to create half pie chart
            region_top.loc[25] = region_top.sum().value

            # reordering based on display order specified in 'const'
            reindexer = list(region_top.index)
            reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
            region_top = region_top.reindex(reindexer, axis=0)

            # bottom pie chart (consumption)
            region_bottom = stor.loc[stor['state'] == region]
            region_bottom = region_bottom.drop("state", axis=1)
            region_bottom = region_bottom.set_index("technology_type_id")
            # adding load value
            region_bottom.loc[21] = float(load.loc[load['state'] == region]['value'])
            # placeholder value, made transparent to create half pie chart
            region_bottom.loc[25] = region_bottom.sum().value

            # reordering based on display order specified in 'const'
            reindexer = list(region_bottom.index)
            reindexer = [x for x in DISPLAY_ORDER if x in reindexer]
            region_bottom = region_bottom.reindex(reindexer, axis=0)

            # determining scaled values for pie chart radii
            region_top = region_top.loc[(region_top != 0).any(axis=1)]
            region_bottom = region_bottom.loc[(region_bottom != 0).any(axis=1)]
            gen_load_ratio = (region_top.sum().value)**(3 / 2) / \
                (region_bottom.sum().value)**(3 / 2)
            if gen_load_ratio >= 1:
                bottom_radius = 1 / gen_load_ratio
                top_radius = 1
            else:
                bottom_radius = 1
                top_radius = 1 * gen_load_ratio
            pie_data[num * 2] = [region_top,
                                 top_radius,
                                 region_scaler[num],
                                 region_positions[num][0],
                                 region_positions[num][1],
                                 True]
            pie_data[num * 2 + 1] = [region_bottom,
                                     bottom_radius,
                                     region_scaler[num],
                                     region_positions[num][0],
                                     region_positions[num][1],
                                     False]

        self.pie_data = pie_data
        self.link_ratio = link_ratio

    def get_legend(self, start_date, end_date):
        """ Generates legend handles for the entire figure. """
        gen_data = self.sqldata.data['gen']
        gen_data = gen_data[(gen_data['timestable'] >= start_date)
                            & (gen_data['timestable'] < end_date)]
        gen_data = gen_data.rename(columns={'timestable': 'timestamp'})
        stor_data = self.sqldata.data['stor']
        stor_data = stor_data[(stor_data['timestamp'] >= start_date)
                              & (stor_data['timestamp'] < end_date)]
        all_data = gen_data.append(stor_data)
        all_data = all_data.drop(['ntndp_zone_id', 'name', 'year'], axis=1)
        all_data = all_data.groupby(['technology_type_id'], as_index=False).sum()
        # only display the 9 most used technologies
        big_tech = all_data.nlargest(9, ['value'])
        big_tech = big_tech.append([{'technology_type_id': 21, 'value': 1}])
        big_tech = list(big_tech['technology_type_id'])
        # ordering according to display order
        big_tech = [x for x in DISPLAY_ORDER if x in big_tech]
        big_tech.reverse()
        big_tech.append(big_tech.pop(0))
        handles = [None] * len(big_tech)
        for j, tech in enumerate(big_tech):
            # mapping each tech to palette specified in const
            handles[j] = mpatches.Patch(color=PALETTE[tech], label=TECH_W_LOAD[tech])
        self.handles = handles

    def map_plotter(self):
        """ Plots arrows and pie charts over the map image to create each \
        individual frame. In future each plot will be made iteratively."""
        # first the image is loaded in
        map_img = plt.imread('templates/img/aust3.png')
        # make the plots
        fig, ax = plt.subplots()
        ax.imshow(map_img, zorder=1)
        plt.axis('off')
        # -- NSW --
        # top pie
        techs = list(self.pie_data[0][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = techs
        values = list(self.pie_data[0][0]['value'])
        ax_pie = fig.add_axes([0.6 - self.pie_data[0][2] / 2,
                               0.37 - self.pie_data[0][2] / 2,
                               self.pie_data[0][2],
                               self.pie_data[0][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[0][5],
                   radius=self.pie_data[0][1], colors=smallpalette)
        patch_counter = len(self.pie_data[0][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[1][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[1][0]['value'])
        ax_pie = fig.add_axes([0.6 - self.pie_data[1][2] / 2,
                               0.37 - self.pie_data[1][2] / 2,
                               self.pie_data[1][2],
                               self.pie_data[1][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[1][5],
                   radius=self.pie_data[1][1], colors=smallpalette)
        patch_counter = patch_counter + len(self.pie_data[1][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # -- QLD ==
        # top pie
        techs = list(self.pie_data[2][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[2][0]['value'])
        ax_pie = fig.add_axes([0.59 - self.pie_data[2][2] / 2,
                               0.55 - self.pie_data[2][2] / 2,
                               self.pie_data[2][2],
                               self.pie_data[2][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[2][5],
                   radius=self.pie_data[2][1], colors=smallpalette)
        patch_counter = len(self.pie_data[2][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[3][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[3][0]['value'])
        ax_pie = fig.add_axes([0.59 - self.pie_data[3][2] / 2,
                               0.55 - self.pie_data[3][2] / 2,
                               self.pie_data[3][2],
                               self.pie_data[3][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[3][5],
                   radius=self.pie_data[3][1], colors=smallpalette)
        patch_counter = patch_counter + len(self.pie_data[3][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # --SA --
        # top pie
        techs = list(self.pie_data[4][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[4][0]['value'])
        ax_pie = fig.add_axes([0.43 - self.pie_data[4][2] / 2,
                               0.43 - self.pie_data[4][2] / 2,
                               self.pie_data[4][2],
                               self.pie_data[4][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[4][5],
                   radius=self.pie_data[4][1], colors=smallpalette)
        patch_counter = len(self.pie_data[4][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[5][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[5][0]['value'])
        ax_pie = fig.add_axes([0.43 - self.pie_data[5][2] / 2,
                               0.43 - self.pie_data[5][2] / 2,
                               self.pie_data[5][2],
                               self.pie_data[5][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[5][5],
                   radius=self.pie_data[5][1], colors=smallpalette)
        patch_counter = patch_counter + len(self.pie_data[5][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # -- TAS ==
        # top pie
        techs = list(self.pie_data[6][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[6][0]['value'])
        ax_pie = fig.add_axes([0.57 - self.pie_data[6][2] / 2,
                               0.13 - self.pie_data[6][2] / 2,
                               self.pie_data[6][2],
                               self.pie_data[6][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[6][5],
                   radius=self.pie_data[6][1], colors=smallpalette)
        patch_counter = len(self.pie_data[6][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[7][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[7][0]['value'])
        ax_pie = fig.add_axes([0.57 - self.pie_data[7][2] / 2,
                               0.13 - self.pie_data[7][2] / 2,
                               self.pie_data[7][2],
                               self.pie_data[7][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[7][5],
                   radius=self.pie_data[7][1], colors=smallpalette)
        patch_counter = patch_counter + len(self.pie_data[7][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # -- VIC ==
        # top pie
        techs = list(self.pie_data[8][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[8][0]['value'])
        ax_pie = fig.add_axes([0.55 - self.pie_data[8][2] / 2,
                               0.25 - self.pie_data[8][2] / 2,
                               self.pie_data[8][2],
                               self.pie_data[8][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[8][5],
                   radius=self.pie_data[8][1], colors=smallpalette)
        patch_counter = len(self.pie_data[8][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # bottom pie
        techs = list(self.pie_data[9][0].index)
        smallpalette = [PALETTE[k] for k in techs]
        used_tech = list(set(used_tech + techs))
        values = list(self.pie_data[9][0]['value'])
        ax_pie = fig.add_axes([0.55 - self.pie_data[9][2] / 2,
                               0.25 - self.pie_data[9][2] / 2,
                               self.pie_data[9][2],
                               self.pie_data[9][2]],
                              zorder=3, aspect='equal')
        ax_pie.pie(values, counterclock=self.pie_data[9][5],
                   radius=self.pie_data[9][1], colors=smallpalette)
        patch_counter = patch_counter + len(self.pie_data[9][0])
        ax_pie.patches[patch_counter - 1].set_alpha(0)
        # defining arrow end locations
        arr_start = [[510, 695],  # NSW to VIC
                     [455, 535],  # NSW to QLD
                     [225, 602],  # SA to VIC
                     [395, 843], ]  # TAS to VIC
        arr_disp = [[-45, 60],
                    [0, -40],
                    [80, 115],
                    [5, 14]]
        # making arrows for trade
        for i, ratio in enumerate(self.link_ratio):
            if ratio < 0:  # if trade in some direction as link is defined
                ax.arrow(arr_start[i][0], arr_start[i][1], arr_disp[i][0],
                         arr_disp[i][1], linewidth=ratio * 10, head_length=5,
                         head_width=7, zorder=5)
            elif ratio > 0:  # if trade in the other direction
                # adjust the arrow so it goes the right way
                x = arr_start[i][0] + arr_disp[i][0]
                y = arr_start[i][1] + arr_disp[i][1]
                dx = -arr_disp[i][0]
                dy = -arr_disp[i][1]
                ax.arrow(x, y, dx, dy,
                         linewidth=abs(ratio) * 10, head_length=5,
                         head_width=7, zorder=5)
            else:  # if there is no trade make a real small arrow with no head
                ax.arrow(arr_start[i][0], arr_start[i][1], arr_disp[i][0],
                         arr_disp[i][1], linewidth=0.3, head_length=0.01,
                         head_width=0.01, zorder=5)
        # plotting the pie chart legend in the top right
        ax_pie_legend = fig.add_axes([0.75, 0.6, 0.15, 0.15], zorder=3, aspect='equal')
        ax_pie_legend.pie([1, 1], colors=[(46 / 255, 49 / 255, 49 / 255, 1),
                                          (171 / 255, 183 / 255, 183 / 255, 1)])
        ax_pie_legend.set_title('Producers', fontsize=8)
        ax_pie_legend.set_xlabel('Consumers', fontsize=8)
        ax_pie_legend.legend(bbox_to_anchor=(-0.25, -0.4),
                             loc=2,
                             borderaxespad=0.,
                             handles=self.handles,
                             ncol=1)
        self.fig = fig

    def main(self, start_date, length):
        """ Generates each frame and combines to generate the animation."""
        plt.clf()  # ensure no figures present
        filenames = []
        start_date = parse(start_date)
        end_date = start_date + timedelta(days=length)
        save_dir = CONFIG['local']['save_dir']
        # generating the hourly timesclices over the previously specified days

        def daterange(start_date, end_date):
            while start_date < end_date:
                yield start_date
                start_date += timedelta(hours=1)
        self.get_legend(start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"))
        # iterating over each hourly timeslice and generating frames
        for single_date in daterange(start_date, end_date):
            date = single_date.strftime("%Y-%m-%d %H:%M")
            self.clean_data(date, date)  # only want to clean for single hour
            self.map_plotter()  # generating frame
            # saving frame
            filename = "frame_" + single_date.strftime("%Y-%m-%d-%H-%M") + ".png"
            filenames = filenames + [filename]
            title = 'OpenCEM Simulation Data for ' + \
                str(length) + ' Days From ' + start_date.strftime("%d/%m/%Y")
            self.fig.suptitle(title)
            self.fig.text(0.45, 0.03, single_date.strftime("%Y-%m-%d %H:%M"))
            self.fig.savefig(os.path.join(save_dir, filename), dpi=150)
            plt.close('all')
        # generating animation
        animation_path = os.path.join(save_dir, 'animation.gif')
        with imageio.get_writer(animation_path, mode='I', fps=3) as writer:
            for filename in filenames:
                image = imageio.imread(os.path.join(save_dir, filename))
                writer.append_data(image)

        # clean up animation files
        frame_list = glob.glob(os.path.join(save_dir, 'frame*'))
        for frame in frame_list:
            os.remove(frame)
