'''Generate sqlite3 file from json file for faster processing of data'''
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

import sys

from json_sqlite import CONFIG, json_parser

# First generate db file from json file
# point to the directory holding the cemo_outputs folder
JSON_PATH = CONFIG['local']['json_path']
sys.path.append(JSON_PATH)
JSON_NAME = CONFIG['local']['json_name']
DATA = json_parser.CemoJsonFile(JSON_NAME)
DATA.process_years()
