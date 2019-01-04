import os
from collections import namedtuple
import json
import pandas as pd
from cemo_outputs import CONFIG, ENGINE

class CemoJsonFile(object):
    def __init__(self, filename="ISP_N_cp_sol.json"):
        self.filename = filename
        self.load_json()
        self.meta = self.json['meta']

    def load_json(self):
        """loads json file (into attribute of class)"""
        json_filepath = os.path.join(CONFIG['local']['json_path'], self.filename)
        with open(json_filepath, "r") as _file:
            self.json = json.load(_file)

    def process_years(self):
        for year in self.meta['Years']:
            year_data = YearData(year)
            year_data.load_data(self)
            year_data.process_vars()

class YearData(object):
    def __init__(self, year="2020"):
        self.year = year
        self.data = None
        self.objective_value = None

    def load_data(self, cemo_json_file):
        self.data = cemo_json_file.json[str(self.year)]
        self.objective_value = self.data['objective_value']

    def process_vars(self):
        for name, variable_map, in VARIABLES.items():
            dataset = VariableDataset(variable_map)
            dataset.parse_all(self)
            dataset.insert_dataset()

class VariableDataset(object):
    def __init__(self, variable_map):
        self.variable_map = variable_map

    def parse_var(self, yeardata, var):
        raw_list = yeardata.data['vars'][var]
        formated_list = [i['index']+[i['value']] for i in raw_list]
        dataframe = pd.DataFrame(formated_list)
        dataframe.columns = self.variable_map.columns
        return dataframe

    def parse_all(self, yeardata):
        series_list = [self.parse_var(yeardata, var) for var in self.variable_map.variable_list]
        self.df = pd.concat(series_list)
        
    def insert_dataset(self, engine=ENGINE):
        self.df.to_sql(self.variable_map.dataset_name, con=engine, if_exists="append", index=None)

#  class factory function for variable dataset metadata
VariableMap = namedtuple("VariableMap",
                            ["dataset_name",
                             "columns",
                             "variable_list"])

VARIABLES = {
    "generation" : VariableMap(
        dataset_name="generation",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestable', 'value'],
        variable_list=["gen_disp", "stor_disp", "hyb_disp"]),
    "scheduled_load" : VariableMap(
        dataset_name="scheduled_load",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestamp', 'value'],
        variable_list=["stor_charge", "hyb_charge"]),
    "storage_level" : VariableMap(
        dataset_name="storage_level",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestamp', 'value'],
        variable_list=["stor_level", "hyb_level"]),                       
    "energy_balance" : VariableMap(
        dataset_name="energy_balance",
        columns=['region_id', 'timestamp', 'value'],
        variable_list=["unserved", "surplus"]),
    "interconnector" : VariableMap(
        dataset_name="interconnector",
        columns=['region_id', 'technology_type_id', 'timestamp', 'value'],
        variable_list=["intercon_disp"]),
    "new_capacity" : VariableMap(
        dataset_name="new_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value'],
        variable_list=["gen_cap_new", "stor_cap_new", "hyb_cap_new"]),
    "existing_capacity" : VariableMap(
        dataset_name="existing_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value'],
        variable_list=["gen_cap_op", "stor_cap_op", "hyb_cap_op"]),
    "exogenous_capacity" : VariableMap(
        dataset_name="exogenous_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value'],
        variable_list=["gen_cap_ret", "gen_cap_ret_neg"])
    }

#need to check - gen_cap_op = existing?
# exogenous capacity?
#interconnector columns?
#"unserved", "surplus" columns?
