def _long2short(data, offset):
    # from IPython import embed
    # embed()
    return abs(data.open[-1 - offset] - data.close[-1 - offset]) > abs(data.open[0 - offset] - data.close[0 - offset]) * 5 and abs(data.open[-1 - offset] - data.close[-1 - offset]) / data.close[-1 - offset] > 0.005     

def top_brake(data):
    return (_long2short(data, 0) and data.close[-1] > data.open[-1]) or \
           (_long2short(data, 1) and data.close[-2] > data.open[-2])

def bottom_brake(data):
    return (_long2short(data, 0) and data.open[-1] > data.close[-1]) or \
           (_long2short(data, 1) and data.open[-2] > data.close[-2])
