from datetime import datetime, timedelta
import traceback

import backtrader as bt
from backtrader import indicators as btind

from zommoros.database import RunList
from zommoros.recipe import *
from zommoros.utils.datetime_util import trim_dt_plus8
from zommoros.utils.math_util import round_down
from zommoros.utils.record import Record
from zommoros.utils.log import get_logger
from zommoros.config import api

# Mean Reversion Strategy(均值回归策略)
class MeReStrategy(bt.Strategy):
    params = (('run_list_id', None),
              ('position_ratio', None),
              ('liquidation_ratio', None),
              ('leverage', None))

    def __init__(self):
        self.logger = get_logger(__name__)
        self.stoch = btind.Stochastic(self.data1, safediv=True)
        self.rsi = btind.RSI(self.data1, period=13, safediv=True)
        self.ema = btind.EMA(self.data1, period=55)
        self.volume_ma = btind.SMA(self.data1.volume, period=21)
        self.order = None
        self.liquidation_price = None
        self.record = None
        self.last_trade_time = None
        self.last_vpos_value = self.broker.getvalue()
        self.live_init()

    def next(self):
        self.broker.load_position(self.data)

        self.logger(f'{self.data._name} | 开盘: {self.data.open[0]} 最高: {self.data.high[0]} 最低: {self.data.low[0]} 收盘: {self.data.close[0]} 成交量:{self.data.volume[0]} [Stoch: K({self.stoch.percK[0]}), D({self.stoch.percD[0]})]; [RSI: {self.rsi[0]}]; [Volume MA: {self.volume_ma[0]}]')
        
        if not self.live_data or self.order:
            return

        ditto_frame = self.last_trade_time == self.data1.datetime.datetime()

        common_cond = not ditto_frame

        open_long_signal = common_cond and self.stoch.percK[-1] < 15 and self.rsi[0] < 25 and self.data.volume[0] > self.volume_ma[0] and self.data.volume[0] < (self.volume_ma[0] * 3.5)
        
        open_short_signal = common_cond and self.stoch.percK[-1] > 85 and self.rsi[0] > 75 and self.data.volume[0] > self.volume_ma[0] and self.data.volume[0] < (self.volume_ma[0] * 3.5)

        if (open_long_signal or open_short_signal) and not self.position:
            if not self.p.leverage and not self.position:
                leverage = int(round_down(20 / self.atratio.closema[0] / 3))
                self.broker.guard_leverage(self.data, 1 if leverage < 1 else 50 if leverage > 50 else leverage)
                self.leverage = self.broker.leverage
            size = self.broker.getcash() * self.p.position_ratio / (self.data.close[0] / self.leverage)
            decimal = len(str(self.amount_min).split('.')[-1])
            trade_size = round_down(size, decimal)
            if trade_size == 0:
                raise Exception('指定的仓位资金已不够进行最低数量的交易!')
            self.logger(f'准备{"买入开多" if open_long_signal else "卖出开空"}, 价格: {self.data.close[0]:.6f}')
            self.is_long = open_long_signal
            if not self.record:
                self.record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
            self.order = self.buy(size=trade_size) if self.is_long else self.sell(size=trade_size)
            self.last_trade_time = self.data1.datetime.datetime()

        if self.position:
            close_long_signal = (self.extreme_price is not None and self.data.close[0] <= self.extreme_price * (1 - self.stop_ratio))
                                
            close_short_signal = (self.extreme_price is not None and self.data.close[0] >= self.extreme_price * (1 + self.stop_ratio))

            self.check_liquidation(self.data.close[0])
            if self.liquidation_signal:
                self.logger(f'{"准备卖出强平" if self.is_long else "准备买入强平"}, {self.data.close[0]:.6f}')
                self.order = self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            self.broker.load_position(self.data)

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
                self.record = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger('Order Canceled/Margin/Rejected')
        
        self.order = None

    def notify_data(self, data, status, *args, **kwargs):
        self.logger(f'{data._name} | Data Status: {data._getstatusname(status)}, Order Status: {status}')
        self.live_data = True if data._getstatusname(status) == 'LIVE' else False

    def check_liquidation(self, current_price):
        self.liquidation_signal = current_price < self.liquidation_price if self.is_long else current_price > self.liquidation_price

    def live_init(self):
        self.broker.load_position(self.data)
        if self.p.leverage:
            self.broker.guard_leverage(self.data, self.p.leverage)
            self.leverage = self.broker.leverage
        self.amount_min = self.broker.get_amount_min(self.data)
        if self.position:
            self.is_long = self.position.size > 0
            self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage

def run():
    record = RunList(type='live')
    record.datetime = datetime.now()

    cp = common_params = {
        # 策略参数:
        'position_ratio': 0.05,
        'liquidation_ratio': 1,
        'leverage': 25,

        # 行情数据参数:
        'dataname': 'DOGE/USDT',
        'name': 'DOGEUSDT',
        'fromdate': datetime.utcnow() - timedelta(hours=1),
    }
    record.arguments = str(common_params)
    record.save()

    cerebro = bt.Cerebro()

    # 策略:
    cerebro.addstrategy(MeReStrategy,
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
        timeframe=bt.TimeFrame.Ticks,
        ohlcv_limit=None
    )
    cerebro.adddata(data)

    data1 = store.getdata(
        dataname=cp['dataname'],
        name=cp['name'],
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
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
