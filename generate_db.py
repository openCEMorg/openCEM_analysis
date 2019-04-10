import sys

from json_sqlite import CONFIG, json_parser
JSON_PATH = CONFIG['local']['json_path']
sys.path.append(JSON_PATH)
JSON_NAME = CONFIG['local']['json_name']
DATA = json_parser.CemoJsonFile(JSON_NAME)
DATA.process_years()

### Then generate report from db file ###
