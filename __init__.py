"""initialises config data and sql engine"""
import os
import configparser
from sqlalchemy import create_engine

MODULE_DIR = os.path.dirname(__file__)

CONFIG = configparser.RawConfigParser()
CONFIG.read(os.path.join(MODULE_DIR, 'config.ini'))

ENGINE = create_engine("sqlite:///{0}".format(CONFIG["local"]["db_path"]))
