def _maxv(data):
    return max(data.open[-1], data.close[-1])
def _minv(data):
    return min(data.open[-1], data.close[-1])
    
def top_split(data):
    return data.open[-2] < data.close[-2] and data.open[0] > data.close[0] and _maxv(data) > data.close[-2] and _maxv(data) > data.open[0] and _minv(data) > data.open[-2] and _minv(data) > data.close[0]

def bottom_split(data):
    return data.open[-2] > data.close[-2] and data.open[0] < data.close[0] and _maxv(data) < data.open[-2] and _maxv(data) < data.close[0] and _minv(data) < data.close[-2] and _minv(data) < data.open[0]
    