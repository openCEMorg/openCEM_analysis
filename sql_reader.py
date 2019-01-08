import pandas as pd
from cemo_outputs import ENGINE

def load_table(table = "generation"):
    """load all data from a particular table"""
    sql = "SELECT * FROM '{0}'".format(table)
    return pd.read_sql(sql.format(table), con = ENGINE)
