import sys
from Json_Parsing import CONFIG, json_parser

### First generate db file from json file ###
#point to the directory holding the cemo_outputs folder
JSON_PATH = CONFIG['local']['json_path']
sys.path.append(JSON_PATH)
JSON_NAME = CONFIG['local']['json_name']
DATA = json_parser.CemoJsonFile(JSON_NAME)
DATA.process_years()

### Then generate report from db file ###
