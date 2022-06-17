import pendulum

from ..init_orator import Model

class Hist(Model):

    __fillable__ = ['run_list_id', 'datetime']

    def fresh_timestamp(self):
        return pendulum.now()

    def fill_ohlvc(self, data):
        self.open = data.open[0]
        self.high = data.high[0]
        self.low = data.low[0]
        self.close = data.close[0]
        self.volume = data.volume[0]
        return self