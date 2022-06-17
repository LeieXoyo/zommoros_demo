import backtrader as bt
import backtrader.indicators as btind

# 乖离率
class BIAS(bt.Indicator):
    lines = ('short', 'long')

    params = (('short_period', 5),
              ('long_period', 45))

    def __init__(self):
        close = self.data.close
        ma_short = btind.SMA(self.data, period=self.p.short_period)
        ma_long = btind.SMA(self.data, period=self.p.long_period)
        self.lines.short = (close - ma_short) / ma_short * 100
        self.lines.long = (close - ma_long) / ma_long * 100