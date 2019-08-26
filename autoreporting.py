'''Automatic report generator for openCEM json files'''
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

import os
from datetime import timedelta

import pandas as pd
import seaborn as sns
from dateutil.parser import parse
from jinja2 import Environment, FileSystemLoader

from json_sqlite import CONFIG
from processing.animating import OutputsAnimator
from processing.const import REGIONS
from processing.loader import MetaData, SqlFile
from processing.plotting import OutputsPlotter


def hover(hover_color="#ffff99"):
    return dict(selector="tr:hover",
                props=[("background-color", "%s" % hover_color)])


styles = [
    hover(),
    dict(selector="th", props=[("font-size", "100%"),
                               ("text-align", "center")])
]


def report_template():
    '''Define standard openCEM report template'''
    # Configure Jinja and ready the loader
    ENV = Environment(
        loader=FileSystemLoader(searchpath="templates")
    )

    # load data from db file
    DATA = SqlFile()
    DATA.load_all_data()

    # Assemble the tamplates to be used
    BASE_TEMPLATE = ENV.get_template("report.html")
    RSV_SECTION_TEMPLATE = ENV.get_template("rsv_section.html")

    # creating reserve margin table
    if (DATA.data['gen'] is None) or (DATA.data['cap'] is None):
        RSV_TABLE = 'Data required for reserve margin calculation was not within the \
                     model outputs file.'
    else:
        DATA.analyse_margin()
        RSV_INFO = DATA.data['reserve']
        MIN_MRG = min(RSV_INFO['min_marg'])
        MIN_T = list(RSV_INFO[RSV_INFO['min_marg'] == MIN_MRG]['min_t'])[0]
        MIN_MRG = round(MIN_MRG * 100, 2)
        RSV_INFO.index = DATA.yrs
        RSV_INFO.columns = ['Minimum Timestamp', 'Minimum <br> Reserve <br> Margin',
                            'Mean <br> Reserve <br> Margin']

    CM = sns.light_palette("orange", reverse=True, as_cmap=True)
    RSV_TABLE = RSV_INFO.style\
                        .set_precision(3) \
                        .background_gradient(cmap=CM,
                                             low=0.4,
                                             high=0.8,
                                             subset=['Mean <br> Reserve <br> Margin'])\
        .background_gradient(cmap=CM,
                             low=0.01,
                             high=0.5,
                             subset=['Minimum <br> Reserve <br> Margin'])
    RSV_TABLE = RSV_TABLE.render()

    # generating yearly plots
    PLOTTER = OutputsPlotter()
    if (DATA.data['gen'] is None) or (DATA.data['cap'] is None):
        CAP_PLOT = "The required data for the yearly capacity and generation plot\
                    was not within the model outputs file."
    else:
        PLOTTER.plot_yearly_cap(DATA)
        CAP_PLOT = '<img src="Yearly_Capacity.png">'

    if DATA.data['cap'] is None or DATA.data['gen'] is None:
        GEN_SLICE = "The required data for the generation plot was not within the \
                     model outputs file."
    else:
        START_DATE = parse(MIN_T, fuzzy=True) - timedelta(days=3)
        PLOTTER.plot_generation_slice(DATA, START_DATE.strftime("%Y-%m-%d"), 7)
        GEN_SLICE = '<img src="Generation_Over_Period.png">'

    # creating transmission tables
    if DATA.data['trans'] is None:
        TRANS_TABLE = "Interconnector transmission data was not within the model \
                       outputs file."
    else:
        DATA.analyse_trans()
        TRADE_DIRECTIONS = len(DATA.data['trade'].index)
        TRANS_TABLE = DATA.data['trade'].style\
                          .set_caption(' Summary of one way transmission between  \
                                        zones in GWh for all simulated years.')\
                          .set_precision(5) \
                          .bar(color='#d65f5f')\
                          .set_table_styles(styles)
        TRANS_TABLE = TRANS_TABLE.render()

    # generating animation
    # slowest part of the process
    # each timestamp as printed as per the Outputs_Animator class
    if DATA.data['trans'] is None or DATA.data['gen'] is None or DATA.data['stor'] is None:
        ANIMATED_GIF = "The required data for the animation was not within the \
                        model outputs file."
    elif TRADE_DIRECTIONS != 8:
        ANIMATED_GIF = "Additional interconnectors have been added. Animation of \
                        this will be included in a later feature."
    else:
        ANIMATOR = OutputsAnimator()
        # animating for 7 days around the min reserve margin
        ANIMATOR.main(START_DATE.strftime("%Y-%m-%d"), 7)
        ANIMATED_GIF = '<img src="animation.gif" height="600" width="800">'

    # getting metadata for the title and description
    META = MetaData()
    META.analyse_meta()
    TITLE = META.simple_meta.pop('Name')
    DESCRIPTION = META.simple_meta.pop('Description')
    SIMPLE_META_TABLE = pd.DataFrame.from_dict(META.simple_meta, orient='index')
    SIMPLE_META_TABLE.columns = ['']
    SIMPLE_META_TABLE = SIMPLE_META_TABLE.style.render()
    LIST_META_TABLE = META.list_meta
    NEW_COLUMN_NAMES = [''] * len(LIST_META_TABLE.columns)
    for i, ass_string in enumerate(list(LIST_META_TABLE.columns)):
        break_counter = 1
        for j, char in enumerate(ass_string):
            if (char == ' ') and (j / break_counter >= 7):
                char = '<br>'
                break_counter = break_counter + 1
            else:
                pass
            NEW_COLUMN_NAMES[i] = NEW_COLUMN_NAMES[i] + char
    LIST_META_TABLE.columns = NEW_COLUMN_NAMES
    LIST_ASSUMPTIONS_TABLE = LIST_META_TABLE.style.render()

    if 'Regional based RET' in META.dict_meta:
        REGIONAL_RET = pd.DataFrame.from_dict(
            META.dict_meta['Regional based RET'], orient='columns')
        REGIONAL_RET.index = DATA.yrs
        REGIONAL_RET.columns = [REGIONS[int(k) - 1] for k in REGIONAL_RET.columns]
        REGIONAL_RET_TABLE = REGIONAL_RET.style.set_caption('Regional Based RET')
        REGIONAL_RET_TABLE = REGIONAL_RET_TABLE.render()
    else:
        REGIONAL_RET_TABLE = "Regional based RET not included."

    # Content to be published
    SECTIONS = list()
    SECTIONS.append(RSV_SECTION_TEMPLATE.render(
        rsv_table=RSV_TABLE,
        min_rsv=MIN_MRG,
        min_time=MIN_T,
        animated_gif=ANIMATED_GIF,
        gen_slice=GEN_SLICE,
        cap_plot=CAP_PLOT,
        trans_pivot_table=TRANS_TABLE,
        simple_assumptions=SIMPLE_META_TABLE,
        list_assumptions=LIST_ASSUMPTIONS_TABLE,
        regional_RET=REGIONAL_RET_TABLE
    ))
    return BASE_TEMPLATE, TITLE, DESCRIPTION, SECTIONS


def main():
    """
    Render a template and write it to file.
    :return:
    """

    save_dir = os.path.join(CONFIG['local']['json_path'],
                            os.path.splitext(CONFIG['local']['json_name'])[0])
    CONFIG['local'].update({'save_dir': save_dir})
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    BASE_TEMPLATE, TITLE, DESCRIPTION, SECTIONS = report_template()
    file_title = TITLE.replace(":", " ")
    fname = os.path.join(save_dir, (file_title + '.html'))
    with open(fname, "w") as _file:
        _file.write(BASE_TEMPLATE.render(
            title=TITLE,
            description=DESCRIPTION,
            sections=SECTIONS
        ))


if __name__ == "__main__":
    main()
