import backtrader as bt
import backtrader.indicators as btind

# Bull and Bear Index
class BullAndBearIndex(bt.Indicator):
    alias = ('BBI',)
    
    lines = ('bbi',)

    params = (('periods', (3, 6, 12, 24)),)

    def __init__(self):
        self.lines.bbi = sum([btind.SMA(self.data, period=p) for p in self.p.periods]) / len(self.p.periods)
