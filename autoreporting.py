import pandas as pd
import matplotlib
from jinja2 import FileSystemLoader, Environment
from datetime import timedelta
from dateutil.parser import parse
from rsv_mrgin_functions import rsv_main
from loader import *
import seaborn as sns

# Configure Jinja and ready the loader
env = Environment(
    loader=FileSystemLoader(searchpath="templates")
)

DATA = Sql_File()
DATA.load_all_data()

# Assemble the tamplates to be used
base_template = env.get_template("report.html")
rsv_section_template = env.get_template("rsv_section.html")

# Getting data to be published
if (DATA.gen is None) or (DATA.cap is None):
    rsv_table = 'Required for reserver margin calculation was not within the \
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

cm = sns.light_palette("orange", reverse=True, as_cmap=True)
rsv_table = rsv_info.style\
                  .set_precision(3) \
                  .background_gradient(cmap=cm,
                                       low=0.4,
                                       high=0.8,
                                       subset=['Mean <br> Reserve <br> Margin'])\
                  .background_gradient(cmap=cm,
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

# Content to be published
title = "Model Results Report"
sections = list()
sections.append(rsv_section_template.render(
    rsv_table = rsv_table,
    min_rsv=min_mrg,
    min_time=min_t,
    animated_gif = animated_gif,
    gen_slice = gen_slice,
    cap_plot = cap_plot,
    trans_pivot_table=trans_table,
))

def main():
    """
    Entry point for the script.
    Render a template and write it to file.
    :return:
    """
    with open("outputs/report.html", "w") as f:
        f.write(base_template.render(
            title=title,
            sections=sections
        ))

if __name__ == "__main__":
    main()
