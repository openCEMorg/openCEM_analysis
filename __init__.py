"""initialises config data and sql engine"""
import os
import configparser
from sqlalchemy import create_engine

MODULE_DIR = os.path.dirname(__file__)

CONFIG = configparser.RawConfigParser()
CONFIG.read(os.path.join(MODULE_DIR, 'config.ini'))

ENGINE = create_engine("sqlite:///{0}".format(CONFIG["local"]["db_path"]))
MYSQL_INSERT = create_engine("mysql://{python_name}:{python_psswd}@{hostname}/opencem_output?unix_socket={socket}".format(**CONFIG['local_mysql']))
MYSQL_CREATE = create_engine("mysql://root:{root_psswd}@{hostname}/opencem_output?unix_socket={socket}".format(**CONFIG['local_mysql']))
