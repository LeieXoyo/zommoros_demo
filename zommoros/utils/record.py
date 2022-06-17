from datetime import datetime

from zommoros.database import TestInfo, TestDetail, LiveInfo, LiveDetail
from zommoros.database.init_orator import db
from zommoros.utils.alert import sendmail_and_dingtalk
from zommoros.utils.retry import retry
    
record_type = {
    'test': [TestInfo, TestDetail],
    'live': [LiveInfo, LiveDetail]
}

class Record:
    def __init__(self, type, run_list_id, data, side, retries=3):
        self.type = type
        self.retries = retries
        self.record = record_type[self.type][0](run_list_id=run_list_id)
        self.record.symbol = data._name
        self.record.side = side
        self.save()

    @property
    def leverage(self):
        return self.record.leverage

    @leverage.setter
    def leverage(self, value):
        self.record.leverage = value

    @property
    def liquidation_price(self):
        return self.record.liquidation_price

    @liquidation_price.setter
    def liquidation_price(self, value):
        self.record.liquidation_price = value

    @retry
    def get_detail(self):
        return record_type[self.type][1]()

    @retry
    def fill_detail(self, detail, dt, order, broker, is_open, last_vpos_value=None):
        detail.datetime = dt
        detail.symbol = self.record.symbol
        detail.price = round(order.executed.price, 6)
        detail.size = self.record.size = abs(round(order.executed.size, 4))
        detail.cost = round(order.executed.value, 2)
        detail.fee = round(order.executed.comm, 2)
        detail.margin = round(order.executed.margin, 2)
        detail.cash = round(broker.getcash(), 2)
        detail.value = self.record.value = round(broker.getvalue(), 2)
        if is_open:
            if not hasattr(self.record, 'open_datetime'):
                self.record.open_datetime = detail.datetime
            self.record.open_price = broker.getposition(order.data).price
        else:
            self.record.close_datetime = detail.datetime
            self.record.close_price = detail.price
        if last_vpos_value is not None:
            self.record.profit = round(detail.value - last_vpos_value, 2)
        if self.type == 'live':
            detail.order_id = order.ccxt_order['id']
            self.send(detail, is_open)
        self.record.details().save(detail)
        self.save()

    @retry
    def save(self):
        db.reconnect(self.record.get_connection_name())
        self.record.save()

    @retry
    def send(self, detail, is_open):
        text_list = [
            detail.symbol,
            detail.datetime,
            f'杠杆倍数: {self.record.leverage}',
            f'{detail.side}, 成交价: {detail.price}, 数量: {detail.size}, 价值: {detail.cost}',
            f'保证金: {detail.margin}, 手续费: {detail.fee}',
            f'可用保证金: {detail.cash}',
            f'期望强平价: {self.record.liquidation_price}' if is_open else f'平仓利润: {self.record.profit}'
        ]
        sendmail_and_dingtalk('Info', '\r\n'.join(text_list))
