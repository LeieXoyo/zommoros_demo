from datetime import datetime

import backtrader as bt
from backtrader import indicators as btind

from zommoros.utils.datetime_util import *
from zommoros.utils.math_util import round_down
from zommoros.utils.record_info import RecordInfo

# MACD Strategy(MACD策略)
class MacdStrategy(bt.Strategy):
    params = (('position_ratio', None),
              ('liquidation_ratio', None),
              ('monitoring_ratio', None),
              ('retracement_ratio', None))

    def __init__(self):
        self.macd = btind.MACD(self.data1)
        self.ema = btind.EMA(self.data1)
        self.order = None
        self.execute_price = None
        self.extreme_price = None
        self.last_trade_time = None
        self.live_init()

    def next(self):
        self.log(f'{self.data._name} | 开盘: {self.data.open[0]} 最高: {self.data.high[0]} 最低: {self.data.low[0]} 收盘: {self.data.close[0]} 成交量:{self.data.volume[0]}')
        
        if not self.live_data or self.order:
            return

        open_long_signal = self.macd.macd[-1] < self.macd.signal[-1] and self.macd.macd[0] > self.macd.signal[0] and self.ema[-1] < self.ema[0]

        open_short_signal = self.macd.macd[-1] > self.macd.signal[-1] and self.macd.macd[0] < self.macd.signal[0] and self.ema[-1] > self.ema[0]

        self.broker.load_position(self.data)
        if self.position:

            close_long_signal = self.extreme_price is not None and \
                                self.execute_price * (1 + self.p.monitoring_ratio) <= self.data.close[0] <= self.extreme_price
                              
            close_short_signal = self.extreme_price is not None and \
                                self.execute_price * (1 - self.p.monitoring_ratio) >= self.data.close[0] >= self.extreme_price

            self.update_extreme_price(self.data)

            self.check_liquidation(self.data.close[0])
            if self.liquidation_signal:
                self.log(f'{"准备卖出强平" if self.is_long else "准备买入强平"}, {self.data.close[0]:.6f}')
            elif self.is_long and (close_long_signal or open_short_signal):
                self.log(f'准备卖出平多, {self.data.close[0]:.6f}')
            elif not self.is_long and (close_short_signal or open_long_signal):
                self.log(f'准备买入平空, {self.data.close[0]:.6f}')
            else:
                return
            self.order = self.close()

        size = self.broker.getcash() * self.p.position_ratio / (self.data.close[0] / self.leverage)
        decimal = len(str(self.amount_min).split('.')[-1])
        trade_size = round_down(size, decimal)
        if trade_size == 0:
            raise Exception('指定的仓位资金已不够进行最低数量的交易!')
        if open_long_signal and self.vaild_time():
            self.log(f'准备买入开多, {self.data.close[0]:.6f}')
            self.is_long = True
            self.order = self.buy(size=trade_size)
        elif open_short_signal and self.vaild_time():
            self.log(f'准备卖出开空, {self.data.close[0]:.6f}')
            self.is_long = False
            self.order = self.sell(size=trade_size)

    def log(self, txt, dt=None):
        dt = dt or self.data.datetime.datetime()
        print(f'{trim_dt_plus8(dt)}, {txt}\n')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            trade_info = RecordInfo('live', self.data, order, self.broker)

            if order.isbuy():
                self.log(f'买入完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                trade_info.side = '买入开多' if abs(self.position.size) == abs(order.executed.size) else '买入强平' if self.liquidation_signal else '买入平空'
            else:
                self.log(f'卖出完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                trade_info.side = '卖出开空' if abs(self.position.size) == abs(order.executed.size) else '卖出强平' if self.liquidation_signal else '卖出平多'

            self.log(f'保证金: {order.executed.margin:.2f}, 手续费: {order.executed.comm:.2f}')
            self.log(f'可用保证金: {self.broker.getcash():.2f}')
            if self.position:
                self.liquidation_price = order.executed.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage
                trade_info.liquidation_price = round(self.liquidation_price, 6)
                self.log(f'期望强平价: {self.liquidation_price:.6f}')
                self.execute_price = order.executed.price
                self.extreme_price = None

            trade_info.save()
            self.last_trade_time = self.data1.datetime.datetime()

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None

    def notify_data(self, data, status, *args, **kwargs):
        self.log(f'{data._name} | Data Status: {data._getstatusname(status)}, Order Status: {status}', datetime.utcnow())
        self.live_data = True if data._getstatusname(status) == 'LIVE' else False

    def check_liquidation(self, current_price):
        self.liquidation_signal = current_price < self.liquidation_price if self.is_long else current_price > self.liquidation_price

    def update_extreme_price(self, data):
        high = data.high[0]
        low = data.low[0]
        if self.is_long and high >= self.execute_price * (1 + self.p.monitoring_ratio) and high > (self.extreme_price if self.extreme_price else self.execute_price):
            self.extreme_price = high
        elif not self.is_long and low <= self.execute_price * (1 - self.p.monitoring_ratio) and low < (self.extreme_price if self.extreme_price else self.execute_price):
            self.extreme_price = low

    def live_init(self):
        self.broker.load_position(self.data)
        self.leverage = self.broker.leverage
        self.amount_min = self.broker.get_amount_min(self.data)
        if self.position:
            self.is_long = self.position.size > 0
            self.execute_price = self.position.price
            self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage

    def vaild_time(self):
        return self.last_trade_time is None or self.last_trade_time != self.data1.datetime.datetime()

def run():
    pass