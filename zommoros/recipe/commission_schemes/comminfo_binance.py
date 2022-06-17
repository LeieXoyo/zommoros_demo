import backtrader as bt

class CommInfoBinance(bt.CommInfoBase):
    params = (
        ('stocklike', False),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('percabs', True),
        ('commission', 0.0002),
        ('automargin', -1),
        ('leverage', 10)
    )

    def _getcommission(self, size, price, pseudoexec):
        value = abs(size) * price
        self.p.margin = value / self.p.leverage
        return value * self.p.commission
