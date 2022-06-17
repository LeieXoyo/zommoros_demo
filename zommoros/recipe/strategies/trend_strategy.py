from datetime import datetime, timedelta
import traceback
import inspect
import sys

import backtrader as bt
from backtrader import indicators as btind

from zommoros.database import RunList
from zommoros.recipe import *
from zommoros.utils.datetime_util import trim_dt_plus8
from zommoros.utils.math_util import round_down
from zommoros.utils.record import Record
from zommoros.utils.log import get_logger
from zommoros.config import api

#  Trend Strategy(趋势策略)
class TrendStrategy(bt.Strategy):
    params = (('run_list_id', None),
              ('position_ratio', None),
              ('liquidation_ratio', None),
              ('leverage', None))

    def __init__(self):
        self.logger = get_logger(__name__)
        self.stoch = btind.Stochastic(self.data1, safediv=True)
        self.rsi = btind.RelativeStrengthIndex(self.data1, safediv=True)
        self.order = None
        self.liquidation_price = None
        self.extreme_price = None
        self.stop_ratio = None
        self.record = None
        self.last_trade_time = None
        self.last_vpos_value = self.broker.getvalue()
        self.live_init()

    def next(self):
        self.logger(f'{self.data._name} | 开盘: {self.data.open[0]} 最高: {self.data.high[0]} 最低: {self.data.low[0]} 收盘: {self.data.close[0]} 成交量:{self.data.volume[0]} [Extreme Price: {self.extreme_price}]; [Stoch: K({self.stoch.percK[0]}), D({self.stoch.percD[0]})]; [RSI: {self.rsi[0]}]')
        
        if not self.live_data or self.order:
            return

        self.broker.guard_position(self.data)

        ditto_frame = self.last_trade_time == self.data1.datetime.datetime()

        open_long_signal = not ditto_frame and self.stoch.percK[-1] > self.stoch.percD[-1] and self.stoch.percK[0] < self.stoch.percD[0] and self.stoch.percK[0] > 80 and self.rsi[0] > 70
                           
        open_short_signal = not ditto_frame and self.stoch.percK[-1] < self.stoch.percD[-1] and self.stoch.percK[0] > self.stoch.percD[0] and self.stoch.percK[0] < 20 and self.rsi[0] < 30

        if (open_long_signal or open_short_signal) and not self.position:
            self.logger(f'准备{"买入开多" if open_long_signal else "卖出开空"}, 价格: {self.data.close[0]:.6f}')
            self.is_long = open_long_signal
            if not self.record:
                self.record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
            trade_size = self.get_trade_size()
            self.order = self.buy(size=trade_size) if self.is_long else self.sell(size=trade_size)
            self.last_trade_time = self.data1.datetime.datetime()

        if self.position:
            if (self.is_long and open_long_signal) or (not self.is_long and open_short_signal):
                self.logger(f'准备{"买入开多" if open_long_signal else "卖出开空"}, 价格: {self.data.close[0]:.6f}')
                trade_size = self.get_trade_size()
                self.order = self.buy(size=trade_size) if self.is_long else self.sell(size=trade_size)
                self.last_trade_time = self.data1.datetime.datetime()
            
            if (self.is_long and open_short_signal) or (not self.is_long and open_long_signal):
                self.logger(f'准备{"买入平空" if open_long_signal else "卖出平多"}, 价格: {self.data.close[0]:.6f}')
                trade_size = abs(self.position.size) / 2
                self.order = self.sell(size=trade_size) if self.is_long else self.buy(size=trade_size)
                self.last_trade_time = self.data1.datetime.datetime()
                
            self.update_extreme_price_and_stop_ratio(self.data)

            close_long_signal = (self.extreme_price is not None and self.data.close[0] <= self.extreme_price * (1 - self.stop_ratio))
                                
            close_short_signal = (self.extreme_price is not None and self.data.close[0] >= self.extreme_price * (1 + self.stop_ratio))

            self.check_liquidation(self.data.close[0])
            if self.liquidation_signal:
                self.logger(f'{"准备卖出强平" if self.is_long else "准备买入强平"}, {self.data.close[0]:.6f}')
            elif self.is_long and close_long_signal:
                self.logger(f'准备卖出平多, {self.data.close[0]:.6f}')
            elif not self.is_long and close_short_signal:
                self.logger(f'准备买入平空, {self.data.close[0]:.6f}')
            else:
                return
            self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            detail = self.record.get_detail()
            dt = trim_dt_plus8(order.data.datetime.datetime())

            if order.isbuy():
                self.logger(f'买入完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                detail.side = '买入开多' if self.position else '买入强平' if self.liquidation_signal else '买入平空'
            else:
                self.logger(f'卖出完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                detail.side = '卖出开空' if self.position else '卖出强平' if self.liquidation_signal else '卖出平多'

            self.logger(f'保证金: {order.executed.margin:.2f}, 手续费: {order.executed.comm:.2f}')
            self.logger(f'可用保证金: {self.broker.getcash():.2f}')

            if self.position:
                self.record.leverage = self.leverage
                self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage
                self.record.liquidation_price = round(self.liquidation_price, 6)
                self.logger(f'期望强平价: {self.record.liquidation_price}')
                self.record.fill_detail(detail, dt, order, self.broker, is_open=True)
            else:
                self.record.fill_detail(detail, dt, order, self.broker, is_open=False, last_vpos_value=self.last_vpos_value)
                self.last_vpos_value = self.broker.getvalue()
                self.liquidation_price = None
                self.extreme_price = None
                self.stop_ratio = None
                self.record = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger('Order Canceled/Margin/Rejected')
        
        self.order = None

    def notify_data(self, data, status, *args, **kwargs):
        self.logger(f'{data._name} | Data Status: {data._getstatusname(status)}, Order Status: {status}')
        self.live_data = True if data._getstatusname(status) == 'LIVE' else False

    def check_liquidation(self, current_price):
        self.liquidation_signal = current_price < self.liquidation_price if self.is_long else current_price > self.liquidation_price

    def update_extreme_price_and_stop_ratio(self, data):
        high = data.high[0]
        low = data.low[0]
        if self.is_long and high >= (self.extreme_price if self.extreme_price else data.close[0]):
            self.extreme_price = high
        elif not self.is_long and low <= (self.extreme_price if self.extreme_price else data.close[0]):
            self.extreme_price = low
        self.stop_ratio = 0.1 - round_down(abs(self.extreme_price - data.close[0]) / self.extreme_price / 0.1) * 0.01

    def get_trade_size(self, position_ratio=None):
        size = self.broker.getcash() * (position_ratio if position_ratio else self.p.position_ratio) / (self.data.close[0] / self.leverage)
        decimal = len(str(self.amount_min).split('.')[-1])
        trade_size = round_down(size, decimal)
        if trade_size == 0:
            raise Exception('指定的仓位资金已不够进行最低数量的交易!')
        return trade_size

    def live_init(self):
        if self.p.leverage:
            self.broker.guard_leverage(self.data, self.p.leverage)
            self.leverage = self.broker.leverage
        self.amount_min = self.broker.get_amount_min(self.data)
        self.broker.load_position(self.data)
        if self.position:
            self.is_long = self.position.size > 0
            self.record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
            self.record.leverage = self.leverage
            self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage
            self.record.liquidation_price = round(self.liquidation_price, 6)
            # self.extreme_price = 0.0
            # self.last_trade_time = datetime(1970, 12, 31, 12, 34, 56)

def run():
    record = RunList(dataname='BTC/USDT', datetime=datetime.now(), type='live')
    record.snapshot = inspect.getsource(sys.modules[__name__])
    record.save()

    cp = common_params = {
        # 策略参数:
        'position_ratio': 0.5,
        'liquidation_ratio': 0.2,
        'leverage': 4,

        # 行情数据参数:
        'dataname': record.dataname,
        'name': record.dataname.replace('/', ''),
        'fromdate': datetime.utcnow() - timedelta(hours=20),
    }

    cerebro = bt.Cerebro()

    # 策略:
    cerebro.addstrategy(TrendStrategy,
                        run_list_id=record.id,
                        position_ratio=cp['position_ratio'],
                        liquidation_ratio=cp['liquidation_ratio'],
                        leverage=cp['leverage'])

    config = {
        'apiKey': api['binance']['key'],
        'secret': api['binance']['secret'],
        'timeout': 30000,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'adjustForTimeDifference': True,
        }
    }

    store = CCXTStore(exchange='binance', currency='USDT', config=config, retries=5, debug=False, sandbox=False)
    broker = store.getbroker()
    cerebro.setbroker(broker)

    data = store.getdata(
        dataname=cp['dataname'],
        name=cp['name'],
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
        fromdate=cp['fromdate'],
        drop_newest=True,
        ohlcv_limit=None
    )
    cerebro.adddata(data)

    data1 = store.getdata(
        dataname=cp['dataname'],
        name=cp['name'],
        timeframe=bt.TimeFrame.Minutes,
        compression=60,
        fromdate=cp['fromdate'],
        drop_newest=True,
        ohlcv_limit=None
    )
    cerebro.adddata(data1)

    record.save_starting_value(round(cerebro.broker.getvalue(), 2))
    print('初始投资组合价值: %.2f' % cerebro.broker.getvalue())
    try:
        cerebro.run()
    except Exception as e:
        record.save_error(traceback.format_exc())
        raise(e)
    print('最终投资组合价值: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candle', barup='red', bardown='green')
    