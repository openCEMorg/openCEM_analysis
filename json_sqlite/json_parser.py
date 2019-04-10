"""Module for parsing json file output, and storing in SQL db"""
import json
import os
from collections import namedtuple

import pandas as pd

from json_sqlite import CONFIG, ENGINE


class CemoJsonFile(object):
    """CEMO JSON File class
    Loads JSON file and contains method to process the yearly data (and meta data in the
    future)"""

    def __init__(self, filename="ISP_N_cp_sol.json"):
        self.filename = filename
        self.load_json()
        self.meta = self.json['meta']
        self.dump_meta()

    def load_json(self):
        """loads json file (into attribute of class)"""
        json_filepath = os.path.join(CONFIG['local']['json_path'], self.filename)
        with open(json_filepath, "r") as _file:
            self.json = json.load(_file)

    def dump_meta(self):
        """ Dumps json metadata into its own json file."""
        fname = os.path.join(CONFIG['local']['json_path'], ('meta_'+self.filename))
        with open(fname, 'w') as _file:
            json.dump(self.meta, _file)

    def process_years(self):
        """Process each year of data contained in the JSON file"""
        for year in self.meta['Years']:
            year_data = YearData(year)
            year_data.load_data(self)
            year_data.process_vars()


class YearData(object):
    """Class to process datasets from each year of output"""

    def __init__(self, year="2020"):
        self.year = year
        self.data = None
        self.objective_value = None

    def load_data(self, cemo_json_file):
        """Method that updates the data attribute. Maybe uncessessary"""
        self.data = cemo_json_file.json[str(self.year)]

    def process_vars(self):
        """Method to process each variable dataset contained in VARIABLES """
        for _, variable_map, in VARIABLES.items():
            dataset = VariableDataset(variable_map)
            dataset.parse_all(self)
            dataset.insert_dataset()


class VariableDataset(object):
    """ Class to parse and insert the data from a particular dataset into an SQL db"""

    def __init__(self, variable_map):
        self.variable_map = variable_map
        self.dataframe = None

    def parse_var(self, yeardata, var):
        """Converts raw list (from json file) containing `index` and `value` items into
        formatted list more suitable for creating a pandas dataframe. Uses this to formatted list
        to generate and return dataframe"""
        raw_list = yeardata.data['vars'][var]
        formated_list = [i['index'] + [i['value']] + [var] + [yeardata.year] for i in raw_list]
        dataframe = pd.DataFrame(formated_list)
        dataframe.columns = self.variable_map.columns
        return dataframe

    def parse_all(self, yeardata):
        """Generates and concatenates all the data frames for dataset into a single data frame"""
        series_list = [self.parse_var(yeardata, var) for var in self.variable_map.variable_list]
        self.dataframe = pd.concat(series_list)

    def insert_dataset(self, engine=ENGINE):
        """Method in insert parsed and concatenated data into SQL db with ENGINE"""
        self.dataframe.to_sql(self.variable_map.dataset_name,
                              con=engine,
                              if_exists="append",
                              index=None)


#  class factory function for variable dataset metadata
VariableMap = namedtuple("VariableMap",
                         ["dataset_name",
                          "columns",
                          "variable_list"])

VARIABLES = {
    "generation": VariableMap(
        dataset_name="generation",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestable', 'value', 'name', 'year'],
        variable_list=["gen_disp", "stor_disp", "hyb_disp"]),
    "scheduled_load": VariableMap(
        dataset_name="scheduled_load",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestamp', 'value', 'name', 'year'],
        variable_list=["stor_charge", "hyb_charge"]),
    "storage_level": VariableMap(
        dataset_name="storage_level",
        columns=['ntndp_zone_id', 'technology_type_id', 'timestamp', 'value', 'name', 'year'],
        variable_list=["stor_level", "hyb_level"]),
    "energy_balance": VariableMap(
        dataset_name="energy_balance",
        columns=['region_id', 'timestamp', 'value', 'name', 'year'],
        variable_list=["unserved", "surplus"]),
    "interconnector": VariableMap(
        dataset_name="interconnector",
        columns=['region_id', 'technology_type_id', 'timestamp', 'value', 'name', 'year'],
        variable_list=["intercon_disp"]),
    "new_capacity": VariableMap(
        dataset_name="new_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value', 'name', 'year'],
        variable_list=["gen_cap_new", "stor_cap_new", "hyb_cap_new"]),
    "existing_capacity": VariableMap(
        dataset_name="existing_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value', 'name', 'year'],
        variable_list=["gen_cap_op", "stor_cap_op", "hyb_cap_op"]),
    "exogenous_capacity": VariableMap(
        dataset_name="exogenous_capacity",
        columns=['ntndp_zone_id', 'technology_type_id', 'value', 'name', 'year'],
        variable_list=["gen_cap_ret", "gen_cap_ret_neg"])
}

# need to check - gen_cap_op = existing?
# exogenous capacity?
# interconnector columns?
#"unserved", "surplus" columns?
