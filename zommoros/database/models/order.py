import pendulum

from ..init_orator import Model

class Order(Model):

    __fillable__ = ['order_id']

    def fresh_timestamp(self):
        return pendulum.now()
