from datetime import datetime, timedelta
import traceback
import inspect
import sys

import backtrader as bt

from zommoros.database import RunList
from zommoros.recipe import *
from zommoros.utils.datetime_util import trim_dt_plus8
from zommoros.utils.math_util import round_down
from zommoros.utils.record import Record
from zommoros.utils.fetch_signals import SignalHook
from zommoros.utils.log import get_logger
from zommoros.config import api

#  TradingView Strategy(基于TV信号的策略)
class TradingViewStrategy(bt.Strategy):
    params = (('run_list_id', None),
              ('position_ratio', None),
              ('liquidation_ratio', None),
              ('leverage', None))

    def __init__(self):
        self.logger = get_logger(__name__)
        self.order = None
        self.liquidation_price = None
        self.record = None
        self.last_vpos_value = self.broker.getvalue()
        self.live_init()
        self.signal_hook = SignalHook()
        self.signal_hook.serve()

    def next(self):
        self.logger.info(f'{self.data._name} | 开盘: {self.data.open[0]} 最高: {self.data.high[0]} 最低: {self.data.low[0]} 收盘: {self.data.close[0]} 成交量:{self.data.volume[0]}')
        
        if not self.live_data or self.order:
            return

        if self.broker.guard_position(self.data) == 'zero':
            self.record = None

        open_long_signal, open_short_signal, close_long_signal, close_short_signal = self.signal_hook.fetch_signal()

        if not self.position:
            if open_long_signal or open_short_signal:
                self.logger.info(f'准备{"买入开多" if open_long_signal else "卖出开空"}, 价格: {self.data.close[0]:.6f}')
                self.is_long = open_long_signal
                self.record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
                trade_size = self.get_trade_size()
                self.order = self.buy(size=trade_size) if self.is_long else self.sell(size=trade_size)

        else:
            self.check_liquidation(self.data.close[0])
            if self.liquidation_signal:
                self.logger.info(f'{"准备卖出强平" if self.is_long else "准备买入强平"}, 价格: {self.data.close[0]:.6f}')
            elif (not self.is_long and open_long_signal) or (self.is_long and open_short_signal) or close_long_signal or close_short_signal:
                self.logger.info(f'准备{"买入平空" if open_long_signal or close_short_signal else "卖出平多"}, 价格: {self.data.close[0]:.6f}')
            else:
                return
            self.order = self.close()
            if (not self.is_long and open_long_signal) or (self.is_long and open_short_signal):
                self.logger.info(f'准备{"买入开多" if open_long_signal else "卖出开空"}, 价格: {self.data.close[0]:.6f}')
                self.is_long = open_long_signal
                self.second_record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
                trade_size = self.get_trade_size()
                self.second_order = self.buy(size=trade_size) if self.is_long else self.sell(size=trade_size)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order is self.order:
                detail = self.record.get_detail()
            elif order is self.second_order:
                detail = self.second_record.get_detail()
            else:
                from IPython import embed
                embed()

            dt = trim_dt_plus8(order.data.datetime.datetime())

            if order.isbuy():
                self.logger.info(f'买入完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                detail.side = '买入开多' if self.position else '买入强平' if self.liquidation_signal else '买入平空'
            else:
                self.logger.info(f'卖出完成, 成交价: {order.executed.price:.6f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}')
                detail.side = '卖出开空' if self.position else '卖出强平' if self.liquidation_signal else '卖出平多'

            self.logger.info(f'保证金: {order.executed.margin:.2f}, 手续费: {order.executed.comm:.2f}')
            self.logger.info(f'可用保证金: {self.broker.getcash():.2f}')

            if self.position:
                self.record.leverage = self.leverage
                self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage
                self.record.liquidation_price = round(self.liquidation_price, 6)
                self.logger.info(f'期望强平价: {self.record.liquidation_price}')
                self.record.fill_detail(detail, dt, order, self.broker, is_open=True)
            else:
                self.record.fill_detail(detail, dt, order, self.broker, is_open=False, last_vpos_value=self.last_vpos_value)
                self.last_vpos_value = self.broker.getvalue()
                self.liquidation_price = None
                self.record = None
                exec(f'self.{order.ccxt_order["type"]}_order = None')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logger.info('Order Canceled/Margin/Rejected')
        
        self.order = None

    def notify_data(self, data, status, *args, **kwargs):
        self.logger.info(f'{data._name} | Data Status: {data._getstatusname(status)}, Order Status: {status}')
        self.live_data = True if data._getstatusname(status) == 'LIVE' else False

    def check_liquidation(self, current_price):
        self.liquidation_signal = current_price < self.liquidation_price if self.is_long else current_price > self.liquidation_price

    def get_trade_size(self, position_ratio=None):
        cash, _ = self.broker.get_balance()
        size = cash * (position_ratio if position_ratio else self.p.position_ratio) / (self.data.close[0] / self.leverage)
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
            self.liquidation_price = self.position.price * eval(f'self.leverage {"-" if self.is_long else "+"} self.p.liquidation_ratio') / self.leverage
            self.record = Record(type='live', run_list_id=self.p.run_list_id, data=self.data, side='做多' if self.is_long else '做空')
            self.record.record.open_price = self.position.price
            self.record.leverage = self.leverage
            self.record.liquidation_price = round(self.liquidation_price, 6)
            self.record.record.size = abs(round(self.position.size, 4))
            self.record.record.value = round(self.broker.getvalue(), 2)
            self.record.save()

def run():
    record = RunList(dataname='BTC/USDT', datetime=datetime.now(), type='live')
    record.snapshot = inspect.getsource(sys.modules[__name__])
    record.save()

    cp = common_params = {
        # 策略参数:
        'position_ratio': 0.5,
        'liquidation_ratio': 0.5,
        'leverage': 20,

        # 行情数据参数:
        'dataname': record.dataname,
        'name': record.dataname.replace('/', ''),
        'fromdate': datetime.utcnow(),
    }

    cerebro = bt.Cerebro()

    # 策略:
    cerebro.addstrategy(TradingViewStrategy,
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

    record.save_starting_value(round(cerebro.broker.getvalue(), 2))
    print('初始投资组合价值: %.2f' % cerebro.broker.getvalue())
    try:
        cerebro.run()
    except Exception as e:
        record.save_error(traceback.format_exc())
        raise(e)
    print('最终投资组合价值: %.2f' % cerebro.broker.getvalue())

    cerebro.plot(style='candle', barup='red', bardown='green')
    