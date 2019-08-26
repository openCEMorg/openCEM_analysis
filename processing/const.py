""" Set of main constant variables required"""
__version__ = "0.9"
__author__ = "Jacob Buddee"
__copyright__ = "Copyright 2019, ITP Renewables, Australia"
__credits__ = ["Jacob Buddee", "Dylan McConnell", "José Zapata"]
__license__ = "GPLv3"
__maintainer__ = "José Zapata"
__email__ = "jose.zapata@itpau.com.au"
__status__ = "Development"

PALETTE = {
    1: '#A3886F',  # biomass
    2: '#F9DCBC',  # ccgt
    3: '#FFCD96',  # ccgt_CCS
    4: '#080808',  # coal_sc
    5: '#4C4C4C',  # coal_sc_CCS
    6: '#8B572A',  # brown_coal
    7: '#957559',  # brown_coal_sc_CCS
    8: '#FDB363',  # ocgt
    9: '#A3980F',  # PV DAT
    10: '#D8C809',  # PV fixed
    11: '#FFF25C',  # PV SAT
    12: '#508313',  # Wind
    13: '#ecc704',  # CST 6h
    14: '#094F87',  # PHES 6 h
    15: '#EEEEEE',  # Battery
    16: '#F35020',  # recip engine,
    17: '#427505',  # Wind high
    18: '#4482B4',  # Hydro
    19: '#F48E1C',  # Gas thermal
    20: '#C5BEBE',  # pumps
    21: '#091587',  # load (red)
    22: '#e1bd03',  # Light gray other tech 1
    23: '#f7d004',  # Light gray other tech 2
    24: '#195F97',  # Light gray other tech 3
    25: '#004878',  # Light gray other tech 4
    26: '#F0F0F0',
    27: '#FFFFFF',
    28: '#282828'
}
PALETTE_2 = PALETTE

TECH_NAMES = {
    1: 'Biomass',
    2: 'CCGT',
    3: 'CCGT CCS',
    4: 'Coal SC',
    5: 'Coal SC CCS',
    6: 'Brown Coal SC',
    7: 'Brown Coal SC CCS',
    8: 'OCGT',
    9: 'Solar PV DAT',
    10: 'Solar PV FFP',
    11: 'Solar PV SAT',
    12: 'Wind (low)',
    13: 'CST 6h',
    14: 'PHES 6h',
    15: 'Battery 2h',
    16: 'Recip Engine',
    17: 'Wind (High)',
    18: 'Hydro',
    19: 'Gas (Thermal)',
    20: 'Pumps',
    21: 'Snowy 2.0',
    22: 'CST 3h',
    23: 'CST 12h',
    24: 'PHES 3h',
    25: 'PHES 12h',
    26: 'Battery 1h',
    27: 'Battery 3h',
    28: 'Black Coal (New)'
}
TECH_W_LOAD = TECH_NAMES  # REVIEW

REGIONS = ["NSW", "QLD", "SA", "TAS", "VIC"]
REGION = {1: 'NSW', 2: 'QLD', 3: 'SA', 4: 'TAS', 5: 'VIC'}
ZONE = {
    1: 'NQ',
    2: 'CQ',
    3: 'SWQ',
    4: 'SEQ',
    5: 'SWNSW',
    6: 'CAN',
    7: 'NCEN',
    8: 'NNS',
    9: 'LV',
    10: 'MEL',
    11: 'CVIC',
    12: 'NVIC',
    13: 'NSA',
    14: 'ADE',
    15: 'SESA',
    16: 'TAS'
}

DISPLAY_ORDER = [
    6, 7, 4, 5, 1, 16, 19, 2, 3, 8, 24, 14, 25, 21, 18, 26, 15, 27, 12, 17, 22,
    13, 23, 9, 10, 11
]
