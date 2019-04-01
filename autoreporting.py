import pandas as pd
import os
from jinja2 import FileSystemLoader, Environment
from datetime import timedelta
from dateutil.parser import parse
from loader import *
import seaborn as sns
from const import REGIONS

# Configure Jinja and ready the loader
ENV = Environment(
    loader=FileSystemLoader(searchpath="templates")
)

DATA = Sql_File()
DATA.load_all_data()

# Assemble the tamplates to be used
base_template = ENV.get_template("report.html")
rsv_section_template = ENV.get_template("rsv_section.html")

# Getting data to be published
if (DATA.gen is None) or (DATA.cap is None):
    rsv_table = 'Data required for reserve margin calculation was not within the \
                 model outputs file.'
else:
    DATA.analyse_margin()
    rsv_info = DATA.reserve
    min_mrg = min(rsv_info['min_marg'])
    min_t = list(rsv_info[rsv_info['min_marg']==min_mrg]['min_t'])[0]
    min_mrg = round(min_mrg*100,2)
    rsv_info.index = DATA.yrs
    rsv_info.columns = ['Minimum Timestamp', 'Minimum <br> Reserve <br> Margin', \
                        'Mean <br> Reserve <br> Margin']

CM = sns.light_palette("orange", reverse=True, as_cmap=True)
rsv_table = rsv_info.style\
                  .set_precision(3) \
                  .background_gradient(cmap=CM,
                                       low=0.4,
                                       high=0.8,
                                       subset=['Mean <br> Reserve <br> Margin'])\
                  .background_gradient(cmap=CM,
                                       low=0.01,
                                       high=0.5,
                                       subset=['Minimum <br> Reserve <br> Margin'])
rsv_table = rsv_table.render()

#generating yearly plots

plotter = outputs_plotter()
if (DATA.gen is None) or (DATA.cap is None):
    cap_plot = "The required data for the yearly capacity and generation plot\
                was not within the model outputs file."
else:
    plotter.plot_yearly_cap(DATA)
    cap_plot = '<img src="../Yearly_Capacity.png">'

if DATA.cap is None or DATA.gen is None:
    gen_slice = "The required data for the generation plot was not within the \
                 model outputs file."
else:
    start_date = parse(min_t, fuzzy=True)-timedelta(days=3)
    plotter.plot_generation_slice(DATA, start_date.strftime("%Y-%m-%d"), 7)
    gen_slice = '<img src="../Generation_Over_Period.png">'

#each animation needs to be generated based on this data, slowest part of process
if DATA.trans is None or DATA.gen is None or DATA.stor is None:
    animated_gif = "The required data for the animation was not within the \
                    model outputs file."
    # make the field empty
else:
    animator = outputs_animator()
    animator.main(start_date.strftime("%Y-%m-%d"), 7)
    animated_gif = "<img src='../Animation/animation.gif' height='600' width='800'>"

#getting transmission data
if DATA.trans is None:
    trans_table = "Interconnector transmission data was not within the model \
                   outputs file."
else:
    DATA.analyse_trans()
    trans_table = DATA.trade.style\
                      .set_caption(' Summary of one way transmission between  \
                                    regions in GWh for all simulated years.')\
                      .set_precision(7) \
                      .bar(color='#d65f5f')
    trans_table = trans_table.render()

#getting metadata for the title and description
DATA.analyse_meta()
TITLE = DATA.simple_meta.pop('Name')
description = DATA.simple_meta.pop('Description')
simple_meta_table = pd.DataFrame.from_dict(DATA.simple_meta, orient='index')
simple_meta_table.columns = ['']
simple_meta_table = simple_meta_table.style.render()
list_meta_table = DATA.list_meta
new_column_names = ['']*len(list_meta_table.columns)
for i, ass_string in enumerate(list(list_meta_table.columns)):
    break_counter = 1
    for j, char in enumerate(ass_string):
        if (char == ' ') and (j/break_counter >= 7):
            char = '<br>'
            break_counter = break_counter + 1
        else:
            pass
        new_column_names[i] = new_column_names[i] + char
list_meta_table.columns = new_column_names
list_assumptions_table = list_meta_table.style.render()
complex_names = ['Years', 'NEM wide RET as ratio', 'NEM wide RET as GWh', \
                 'Regional based RET', 'System emission limit']

if 'Regional based RET' in DATA.dict_meta:
    regional_RET = pd.DataFrame.from_dict(DATA.dict_meta['Regional based RET'], orient = 'columns')
    regional_RET.index = DATA.yrs
    regional_RET.columns = [REGIONS[int(k)-1] for k in regional_RET.columns]
    regional_RET_table = regional_RET.style.set_caption('Regional Based RET')
    regional_RET_table = regional_RET_table.render()
else:
    regional_RET_table = "Regional based RET not included."

# Content to be published
SECTIONS = list()
SECTIONS.append(rsv_section_template.render(
    rsv_table=rsv_table,
    min_rsv=min_mrg,
    min_time=min_t,
    animated_gif=animated_gif,
    gen_slice=gen_slice,
    cap_plot=cap_plot,
    trans_pivot_table=trans_table,
    simple_assumptions=simple_meta_table,
    list_assumptions=list_assumptions_table,
    regional_RET=regional_RET_table
))



def main():
    """
    Entry point for the script.
    Render a template and write it to file.
    :return:
    """
    file_title = TITLE.replace(":", " ")
    fname = os.path.join("outputs/", (file_title+'_report.html'))
    with open(fname, "w") as _file:
        _file.write(base_template.render(
            title=TITLE,
            description=description,
            sections=SECTIONS
        ))

if __name__ == "__main__":
    main()
