import backtrader as bt
import backtrader.indicators as btind

# ATR Ratio(波动比率)
class ATRatio(bt.Indicator):    
    lines = ('atratio', 'closema', 'ceratio')

    params = (('ema_period', 14),
              ('atr_period', 14))

    def __init__(self):
        close = self.data.close
        ema = btind.EMA(period=self.p.ema_period)
        atr = btind.ATR(period=self.p.atr_period)
        self.lines.atratio = atr / close * 100
        self.lines.closema = abs(ema - close) / close * 100
        self.lines.ceratio = self.l.closema / self.l.atratio

    def __str__(self):
        items = list()
        items.append('---')
        items.append(f'ATRatio: {self.l.atratio[0]}')
        items.append(f'ClosEMA: {self.l.closema[0]}')
        items.append(f'CERatio: {self.l.ceratio[0]}')
        items.append('---')
        return '\n'.join(items)
        