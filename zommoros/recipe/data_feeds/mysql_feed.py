import datetime

import backtrader as bt
from backtrader.feed import DataBase

from zommoros.database import Hist
from zommoros.utils.datetime_util import dt_from_str_to_num

class MySQLData(DataBase):
    params = (
        ('name', ''),
        ('fromdate', datetime.datetime.min),
        ('todate', datetime.datetime.max),
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1),
        ('run_list_id', None),
    )

    def __init__(self, *args, **kwargs):
        self.hists = []
        self.empty = False

    def start(self):
        self.hists = self.load_data_from_db(self.p.run_list_id, self.p.fromdate, self.p.todate)

    def _load(self):
        if self.empty:
            return False
        try:
            hist = next(self.hists)
        except StopIteration:
            return False
        self.lines.datetime[0] = dt_from_str_to_num(hist.datetime)
        self.lines.open[0] = float(hist.open)
        self.lines.high[0] = float(hist.high)
        self.lines.low[0] = float(hist.low)
        self.lines.close[0] = float(hist.close)
        self.lines.volume[0] = float(hist.volume)
        return True

    def load_data_from_db(self, run_list_id, fromdate, todate):
        hists = Hist.where('run_list_id', run_list_id).where_between('datetime', [fromdate, todate]).get()
        return iter(hists)
        