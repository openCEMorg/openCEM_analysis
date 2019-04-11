'''Generate sqlite3 file from json file for faster processing of data'''

import sys

from json_sqlite import CONFIG, json_parser

# First generate db file from json file
# point to the directory holding the cemo_outputs folder
JSON_PATH = CONFIG['local']['json_path']
sys.path.append(JSON_PATH)
JSON_NAME = CONFIG['local']['json_name']
DATA = json_parser.CemoJsonFile(JSON_NAME)
DATA.process_years()
