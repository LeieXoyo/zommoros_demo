import backtrader as bt

class CommInfoOkex(bt.CommInfoBase):
    params = (
        ('stocklike', False),
        ('commtype', bt.CommInfoBase.COMM_PERC),
        ('percabs', True),
        ('mult', 0.01),
        ('commission', 0.0002),
        ('automargin', -1),
        ('leverage', 10),
        ('contract_val', 0.01),
    )

    def _getcommission(self, size, price, pseudoexec):
        value = abs(size) * price * self.p.contract_val
        self.p.margin = value / self.p.leverage
        return value * self.p.commission
