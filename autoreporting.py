import pandas as pd
from jinja2 import FileSystemLoader, Environment
from datetime import timedelta
from dateutil.parser import parse
from rsv_mrgin_functions import rsv_main
from loader import *

# Configure Jinja and ready the loader
env = Environment(
    loader=FileSystemLoader(searchpath="templates")
)

DATA = Sql_File()

# Assemble the tamplates to be used
base_template = env.get_template("report.html")
rsv_section_template = env.get_template("rsv_section.html")

# Getting data to be published
min_t, min_mrg = rsv_main(2030, 2045)
min_t = min_t[min_mrg.index(max(min_mrg))]
min_mrg = round(max(min_mrg)*100,2)


DATA.get_cap()
DATA.get_gen()
#generating yearly plots
start_date = parse(min_t, fuzzy=True)
DATA.make_yearly_plot(start_date.strftime("%Y-%m-%d"), 1)

DATA.cap = None
DATA.gen = None

#each animation needs to be generated based on this data, can be quite slow
start_date = start_date-timedelta(days=1)
DATA.animate(start_date.strftime("%Y-%m-%d"), 3)

#getting transmission data


DATA.get_trans()
DATA.analyse_trans()
DATA.trans = None
table = DATA.trade.to_html()

# Content to be published
title = "Model Results Report"
sections = list()
sections.append(rsv_section_template.render(
    min_rsv=min_mrg,
    min_time=min_t,
    trans_pivot_table=table,
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
