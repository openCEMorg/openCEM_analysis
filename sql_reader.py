import pandas as pd
from cemo_outputs import ENGINE, MYSQL_INSERT

def load_table(table = "generation", engine=MYSQL_INSERT):
    """load all data from a particular table"""
    sql = "SELECT * FROM {0}".format(table)
    return pd.read_sql(sql.format(table), con=engine, index_col="timestamp")

def load_generation(year=2020, engine=MYSQL_INSERT):
    sql = "SELECT g.timestamp, nz.text_id as ntndp_zone, r.text_id as region, tt.text_id as technology_type, g.value FROM generation g "\
          "INNER JOIN ntndp_zone nz "\
              "ON nz.id = g.ntndp_zone_id "\
          "INNER JOIN region r "\
              "ON r.id = nz.region_id "\
          "INNER JOIN technology_type tt "\
              "ON tt.id = g.technology_type_id "\
          "WHERE g.timestamp > '{0}-1-1' "\
                "AND g.timestamp <= '{1}-1-1'".format(year, year+1)
    return pd.read_sql(sql, con=engine, index_col="timestamp")
