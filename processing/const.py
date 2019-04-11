""" Set of main constant variables required"""
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

PALETTE = {1: (161 / 255, 135 / 255, 111 / 255, 1),  # biomass
           2: (251 / 255, 177 / 255, 98 / 255, 1),  # ccgt
           3: (251 / 255, 177 / 255, 98 / 255, 0.75),  # ccgt_sc
           4: (25 / 255, 25 / 255, 25 / 255, 1),  # coal_sc
           5: (25 / 255, 25 / 255, 25 / 255, 0.75),  # coal_sc_scc
           6: (137 / 255, 87 / 255, 45 / 255, 1),  # brown_coal_sc
           7: (137 / 255, 87 / 255, 45 / 255, 0.75),   # brown_coal_sc_scc
           8: (253 / 255, 203 / 255, 148 / 255, 1),  # ocgt
           9: (220 / 255, 205 / 255, 0, 0.6),  # PV DAT
           10: (220 / 255, 205 / 255, 0 / 255, 0.8),  # PV fixed
           11: (220 / 255, 205 / 255, 0 / 255, 1),  # PV SAT
           12: (67 / 255, 116 / 255, 14 / 255, 1),  # Wind
           13: (1, 209 / 255, 26 / 255, 1),  # CST 6h
           14: (137 / 255, 174 / 255, 207 / 255, 1),  # PHES 6 h
           15: (43 / 255, 161 / 255, 250 / 255, 1),  # Battery
           16: (240 / 255, 79 / 255, 35 / 255, 1),  # recip engine,
           17: (52 / 255, 76 / 255, 55 / 255, 1), #(128 / 255, 191 / 255, 1, 1),  # Wind high
           18: (75 / 255, 130 / 255, 178 / 255, 1),  # Hydro
           19: (241 / 255, 140 / 255, 31 / 255, 1),  # Gas thermal
           20: (0 / 255, 96 / 255, 1, 1),  # pumps
           21: (162 / 255, 47 / 255, 47 / 255, 1),  # load (red)
           22: (140 / 255, 140 / 255, 140 / 255, 1),  # Light gray other tech 1
           23: (145 / 255, 145 / 255, 145 / 255, 1),  # Light gray other tech 2
           24: (150 / 255, 150 / 255, 150 / 255, 1),  # Light gray other tech 3
           25: (160 / 255, 160 / 255, 160 / 255, 1),  # Light gray other tech 4
           }
PALETTE_2 = {1: (161 / 255, 135 / 255, 111 / 255, 1),  # biomass
             2: (251 / 255, 177 / 255, 98 / 255, 1),  # ccgt
             3: (251 / 255, 177 / 255, 98 / 255, 0.75),  # ccgt_sc
             4: (25 / 255, 25 / 255, 25 / 255, 1),  # coal_sc
             5: (25 / 255, 25 / 255, 25 / 255, 0.75),  # coal_sc_scc
             6: (137 / 255, 87 / 255, 45 / 255, 1),  # brown_coal_sc
             7: (137 / 255, 87 / 255, 45 / 255, 0.75),   # brown_coal_sc_scc
             8: (253 / 255, 203 / 255, 148 / 255, 1),  # ocgt
             9: (220 / 255, 205 / 255, 0, 0.6),  # PV DAT
             10: (220 / 255, 205 / 255, 0 / 255, 0.8),  # PV fixed
             11: (220 / 255, 205 / 255, 0 / 255, 1),  # PV SAT
             12: (67 / 255, 116 / 255, 14 / 255, 1),  # Wind
             13: (1, 209 / 255, 26 / 255, 1),  # CST 6h
             14: (137 / 255, 174 / 255, 207 / 255, 1),  # PHES 6 h
             15: (43 / 255, 161 / 255, 250 / 255, 1),  # Battery
             16: (240 / 255, 79 / 255, 35 / 255, 1),  # recip engine,
             17: (52 / 255, 76 / 255, 55 / 255, 1), #(128 / 255, 191 / 255, 1, 1),  # Wind high
             18: (75 / 255, 130 / 255, 178 / 255, 1),  # Hydro
             19: (241 / 255, 140 / 255, 31 / 255, 1),  # Gas thermal
             20: (0 / 255, 96 / 255, 1, 1),  # pumps
             21: (1 / 255, 50 / 255, 67 / 255, 1),  # Snowy2.0
             22: (140 / 255, 140 / 255, 140 / 255, 1),  # Light gray other tech 1
             23: (145 / 255, 145 / 255, 145 / 255, 1),  # Light gray other tech 2
             24: (150 / 255, 150 / 255, 150 / 255, 1),  # Light gray other tech 3
             25: (160 / 255, 160 / 255, 160 / 255, 1),  # Light gray other tech 4
             }
TECH_NAMES = {1:'Biomass',
              2:'CCGT',
              3:'CCGT CCS',
              4:'Coal SC',
              5:'Coal SC CCS',
              6:'Brown Coal SC',
              7:'Brown Coal SC CCS',
              8:'OCGT',
              9:'Solar PV DAT',
              10:'Solar PV FFP',
              11:'Solar PV SAT',
              12:'Wind',
              13:'CST 6h',
              14:'PHES 6h',
              15:'Battery 2h',
              16:'Recip Engine',
              17:'Wind (High)',
              18:'Hydro',
              19:'Gas (Thermal)',
              20:'Pumps',
              21:'Snowy 2.0'
              }
TECH_W_LOAD = {1:'Biomass',
               2:'CCGT',
               3:'CCGT CCS',
               4:'Coal SC',
               5:'Coal SC CCS',
               6:'Brown Coal SC',
               7:'Brown Coal SC CCS',
               8:'OCGT',
               9:'Solar PV DAT',
               10:'Solar PV FFP',
               11:'Solar PV SAT',
               12:'Wind (High)',
               13:'CST 6h',
               14:'PHES 6h',
               15:'Battery 2h',
               16:'Recip Engine',
               17:'Wind H',
               18:'Hydro',
               19:'Gas (Thermal)',
               20:'Pumps',
               21:'Load'
               }
REGIONS = ["NSW", "QLD", "SA", "TAS", "VIC"]

DISPLAY_ORDER = [6, 7, 4, 5, 1, 16, 19, 2, 3, 8, 15, 18, 14, 17, 12, 13, 9, 10, \
                11, 20, 21, 22, 23, 24, 25]
