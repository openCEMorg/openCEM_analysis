'''Functions to load database data for reports'''
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

import json
import os
import sqlite3

import numpy as np
import pandas as pd
from dateutil.parser import parse

from json_sqlite import CONFIG

# disabling unnecessary warnings
pd.options.mode.chained_assignment = None  # default='warn'


class DateInput():
    """Date Input Class
    Parses a start and end date flexibly from most accepted date formats, into
    datetime objects. Will give preference to U.S. date formats."""

    def __init__(self, start_date, end_date):
        if start_date is None and end_date is None:
            start_date = '2020-01-01'
            end_date = '2045-12-31'
        else:
            try:
                parse(start_date)
                try:
                    parse(end_date)
                except (ValueError, TypeError):
                    end_date = start_date
            except (ValueError, TypeError):
                error_statement = "Either two dates have not been inputted as \
                arguments or one of the dates cannot be recognised as a date. \
                Please input two dates in a format such as 'YYYY-MM-DD.'"
                print(error_statement)
        self.start_obj = parse(start_date)
        self.start = self.start_obj.strftime("%Y-%m-%d %H:%M:%S")
        self.end_obj = parse(end_date)
        self.end = self.end_obj.strftime("%Y-%m-%d %H:%M:%S")


class MetaData():
    """ Class to load and hold json metadata. """

    def __init__(self):
        self.meta_name = os.path.join(CONFIG['local']['json_path'],
                                      ('meta_' + CONFIG['local']['json_name']))
        with open(self.meta_name, 'r') as _file:
            self.meta = json.load(_file)
        self.yrs = self.meta['Years']
        self.dict_meta = []
        self.list_meta = []
        self.simple_meta = []

    def analyse_meta(self):
        """ Breaks up metadata by datatype for input to html tables via \
        pandas.style """
        dict_meta = {}
        list_meta = {}
        simple_meta = {}
        for key, value in self.meta.items():
            if isinstance(value, dict):
                dict_meta[key] = value
            elif isinstance(value, list):
                if len(value) == len(self.yrs):
                    list_meta[key] = value
                else:
                    pass
            elif value is None:
                pass
            else:
                simple_meta[key] = value
        list_meta = pd.DataFrame.from_dict(list_meta)
        if isinstance(self.yrs, list):
            list_meta.set_index('Years')
            list_meta.index.name = ''
        else:
            pass
        self.dict_meta = dict_meta
        self.list_meta = list_meta
        self.simple_meta = simple_meta


class SqlFile():
    """ Sql File class
    Loads and hold data from sql file and meta json data in pandas dataframes.
    Methods for basic analysis of some data."""

    def __init__(self):
        # load file names from config
        self.db_name = CONFIG['local']['db_path']
        # determing which tables are in sql file
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = list(cursor.fetchall())
        names = [i[0] for i in names]
        self.tables = names
        # defining years from MetaData
        self.yrs = MetaData().yrs
        self.data = {'trans': pd.DataFrame(),
                     'gen': pd.DataFrame(),
                     'stor': pd.DataFrame(),
                     'cap': pd.DataFrame(),
                     'trade': pd.DataFrame(),
                     'reserve': pd.DataFrame()}

    def get_trans(self):
        """ Loads transmission data."""
        if 'interconnector' in self.tables:  # if table exists
            conn = sqlite3.connect(self.db_name)
            query = "select * from interconnector"
            self.data['trans'] = pd.read_sql_query(query, conn)
        else:
            self.data['trans'] = None

    def get_gen(self):
        """ Loads generation data."""
        if 'generation' in self.tables:
            conn = sqlite3.connect(self.db_name)
            query = "select * from generation"
            self.data['gen'] = pd.read_sql_query(query, conn)
        else:
            self.data['gen'] = None

    def get_stor(self):
        """ Loads storage data."""
        if 'scheduled_load' in self.tables:
            conn = sqlite3.connect(self.db_name)
            query = "select * from scheduled_load where name = 'stor_charge'"
            self.data['stor'] = pd.read_sql_query(query, conn)
        else:
            self.data['stor'] = None

    def get_cap(self):
        """ Loads capacity data."""
        if 'existing_capacity' in self.tables and 'new_capacity' in self.tables:
            conn = sqlite3.connect(self.db_name)
            query = "select * from existing_capacity"
            self.data['cap'] = pd.read_sql_query(query, conn)
        else:
            self.data['cap'] = None

    def load_all_data(self):
        """ Single method for loading all tables data """
        self.get_cap()
        self.get_stor()
        self.get_gen()
        self.get_trans()

    def analyse_trans(self):
        """Generates dataframe of transmission between regions. Optimised for \
         input to pandas.style html tables."""
        trans = self.data['trans']
        trans = trans.drop(['name', 'timestamp'], axis=1)
        map_dict = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
        trans['region_id'] = trans['region_id'].map(map_dict)
        trans['technology_type_id'] = trans['technology_type_id'].map(map_dict)
        trans['value'] = trans['value'] / 10**3
        trans = trans.pivot_table(
            values='value',
            index=['region_id', 'technology_type_id'],
            columns='year', aggfunc=np.sum
        )
        # inserting breaks for html formatting
        trans.index.names = ['  Exported <br> From  ', '  Imported <br> To  ']
        trans.columns.names = ['Simulated <br> Years']
        self.data['trade'] = trans

    def analyse_margin(self):
        """ Generates dataframe of minimum reserve margin, the time of this \
        minimum and the mean reserve margin for each year. """
        min_mrg = [None] * len(self.yrs)
        mean_mrg = [None] * len(self.yrs)
        min_t = [None] * len(self.yrs)
        for i, year in enumerate(self.yrs):
            gen = self.data['gen']
            gen = gen[gen['year'] == year]
            gen = gen.groupby(['timestable'], as_index=False).sum()
            cap = self.data['cap']
            cap = cap[cap['year'] == year]
            total_cap = cap['value'].sum()
            rsv_mrg = gen
            rsv_mrg['value'] = rsv_mrg['value'].apply(lambda x: 1 - x / total_cap)
            min_mrg[i] = min(rsv_mrg['value'])
            mean_mrg[i] = rsv_mrg['value'].mean()
            min_t[i] = rsv_mrg.loc[rsv_mrg['value'].idxmin]['timestable']
        rsv_info = {'min_t': min_t, 'min_marg': min_mrg, 'MARG_MEAN': mean_mrg}
        rsv_info = pd.DataFrame(data=rsv_info)
        self.data['reserve'] = rsv_info
