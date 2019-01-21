import sqlite3
import pandas as pd
from dateutil.parser import parse

def sql_reader(query):
    conn = sqlite3.connect("test.db")
    df = pd.read_sql_query(query, conn)
    return df

def csv_output(df, table_name):
    fname = table_name + '.csv'
    df.to_csv(fname)

def is_date(string):
    try:
        parse(string)
        return True
    except (TypeError, ValueError):
        return False
