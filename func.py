""" Set of general functions used throughout."""

def zone_to_region(frame):
    """ Creates a condition which allows for zone values to be mapped to \
    regions"""
    if frame.columns.values[0] == 'ntndp_zone_id':
        d_qld = dict.fromkeys([1, 2, 3, 4], "QLD")
        d_nsw = dict.fromkeys([5, 6, 7, 8], "NSW")
        d_vic = dict.fromkeys([9, 10, 11, 12], "VIC")
        d_sa = dict.fromkeys([13, 14, 15], "SA")
        d_tas = dict.fromkeys([16], "TAS")
        state_cond = {**d_qld, **d_nsw, **d_vic, **d_sa, **d_tas}
        frame["ntndp_zone_id"] = frame["ntndp_zone_id"].map(state_cond)
        frame_group = ['ntndp_zone_id', 'technology_type_id', 'timestamp']
        frame = frame.groupby(frame_group, as_index=False).sum()
        frame = frame.rename(columns={'ntndp_zone_id':'state'})
    else:
        pass
    return frame
