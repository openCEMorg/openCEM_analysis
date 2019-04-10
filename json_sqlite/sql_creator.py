import os
from sqlalchemy import Column, Integer, String, MetaData, create_engine, Table, ForeignKey, Numeric, DateTime
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from . import CONFIG

def create_test_table():
    path = os.path.join(CONFIG["local"]["data_path"], "test_db2.db")
    if os.path.exists(path):
        os.remove(path)
    engine = create_engine("sqlite:///{0}".format(path))
    metadata = MetaData()

    for table in[ "region", "connection_type","schedule_type", "resource_type", "source", "fuel_type", "wind_bubble", "isp_re_zone"]:
        base_table(table, metadata)

    for table_name, foreign_keys in {"ntndp_zone"       : ['region'],
                                     "demand_scenario"  : ['source'],
                                     "technology_type"  : ['resource_type', 'connection_type', 'schedule_type'],
                                     "ntndp_wind_bubbles": ['ntndp_zone', 'wind_bubble'],
                                     "ntndp_isp_zones"  : ['ntndp_zone', 'isp_re_zone']}.items():
        table=base_table(table_name, metadata)
        add_foreign_keys(table, metadata, foreign_keys=foreign_keys)

    for table_name, (foreign_keys, columns) in {"opex"					:	[['source', 'technology_type'], {"fom": Numeric, "vom": Numeric}],
                                                "build_limit"			:	[['isp_re_zone'], {'wind_high': Numeric, 'wind_medium':Numeric,'solar':Numeric, 'phes':Numeric}],
                                                "transmission":	[['isp_re_zone','ntndp_zone'], {'transmission_limit':Numeric,'transmission_cost':Numeric}]}.items():
        table=base_table(table_name, metadata)
        add_foreign_keys(table, metadata, foreign_keys=foreign_keys)
        add_columns(table, metadata, columns)

    for table_name, (foreign_keys, columns) in {"wind_and_solar_traces"		:	[['technology_type', 'source', 'ntndp_zone','wind_bubble', 'isp_re_zone'], {"mw":Numeric, "timestamp": DateTime}],
                                                "demand_and_rooftop_traces"	:	[['region', 'demand_scenario'],{"poe10": Numeric, 'rooftop_solar': Numeric, "timestamp": DateTime}], 
                                                "capex": [['demand_scenario', 'technology_type','ntndp_zone'], {"capex": Numeric,"year":Integer}]}.items():
        table=data_table(table_name, metadata)
        add_foreign_keys(table, metadata, foreign_keys=foreign_keys)
        add_columns(table, metadata, columns)
    metadata.create_all(engine)

def base_table(table_name, metadata):
    return Table(table_name, metadata,
           Column('id', Integer, primary_key=True),
           Column('text_id', String(50), nullable=False),
           Column('name', String(50), nullable=False)
           )

def data_table(table_name, metadata):
    return Table(table_name, metadata,
           Column('id', Integer, primary_key=True))

def add_foreign_keys(table, metadata, foreign_keys = ["region"]):
    for fk in foreign_keys:
        table.append_column(Column('{0}_id'.format(fk), Integer, ForeignKey("{0}.id".format(fk)), nullable=False))

def add_columns(table, metadata, columns):
    for col, dtype in columns.items():
        table.append_column(Column(col, dtype, nullable=True))
