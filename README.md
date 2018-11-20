# CEMO output post processing   
This repository contains a set of utilities to extract information from the JSON output of CEMO.
# Features
The following is a draft set of features desired for this project:
## Basic data
- Existing capacity (per zone or region, per technology, per year)
- New capacity (per zone or region, per technology, per year)
- Generation (per zone or region, per technology, per year)

## Metrics
- Spillage from renewable energy (per zone or per region, per technology, per year)
- Reserve margins (per region, per year)
- Net transmission imports per region per year
- Unserved energy (per region, per year)
- Surpulus energy (per region ,per year)
- Curtailed distributed pv (per region, per year) *Not yet implemented*

## Graphs
- Capacity per year
- Generation per year
- Costs per year
- Emissions per year

# Requirements
- The scripts must be written in Python3
- Scripts shall score 8 or above in pylint 
- Scripts shall feature unit testing with pytest.