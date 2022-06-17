import pendulum

from ..init_orator import Model

class TestDetail(Model):

    def fresh_timestamp(self):
        return pendulum.now()
