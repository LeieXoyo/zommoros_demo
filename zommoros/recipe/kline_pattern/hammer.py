def top_hammer(data):
    return ((data.high[0] - max(data.open[0], data.close[0])) > abs(data.open[0] - data.close[0]) * 5 and (data.high[0] - max(data.open[0], data.close[0])) > (min(data.open[0], data.close[0]) - data.low[0]) * 2) or \
           ((data.high[-1] - max(data.open[-1], data.close[-1])) > abs(data.open[-1] - data.close[-1]) * 5 and (data.high[-1] - max(data.open[-1], data.close[-1])) > (min(data.open[-1], data.close[-1]) - data.low[-1]) * 2)
def bottom_hammer(data):
    return ((min(data.open[0], data.close[0]) - data.low[0]) > abs(data.open[0] - data.close[0]) * 5 and (min(data.open[0], data.close[0]) - data.low[0]) > (data.high[0] - max(data.open[0], data.close[0])) * 2) or \
           ((min(data.open[-1], data.close[-1]) - data.low[-1]) > abs(data.open[-1] - data.close[-1]) * 5 and (min(data.open[-1], data.close[-1]) - data.low[-1]) > (data.high[-1] - max(data.open[-1], data.close[-1])) * 2)