#determines which indexing field the variable of interest is in
def determine_field(variable):
    #defining which record is in which field
    set = ["regions", "zones", "all_tech","t","zones_in_regions","fuel_gen_tech"
    , "retire_gen_tech", "nobuild_gen_tech", "hyb_tech", "stor_tech",
    "gen_tech_in_zones", "fuel_tech_in_zones", "retire_tech_in_zones",
    "hyb_tech_in_zones", "stor_tech_in_zones", "region_intercons"]
    complex_set = ["zones_per_region", "gen_tech_per_zone",
    "fuel_gen_tech_per_zone", "retire_gen_tech_per_zone", "hyb_tech_per_zone",
    "stor_tech_per_zone", "intercon_per_region"]
    #parameters aren't currently required so not checking for these
    vars = ["gen_cap_new", "gen_cap_op", "stor_cap_new", "stor_cap_op",
    "hyb_cap_new", "hyb_cap_op", "gen_cap_ret", "gen_cap_ret_neg", "gen_disp",
    "stor_disp", "stor_charge", "stor_level", "hyb_disp", "hyb_charge",
    "hyb_level", "unserved", "surplus", "intercon_disp"]
    #checking which field the variable is in and defining return string
    if variable in vars:
        field = "vars"
    elif variable in set:
        field = "set"
    elif variable in complex_set:
        field = "complex_set"
    return field
