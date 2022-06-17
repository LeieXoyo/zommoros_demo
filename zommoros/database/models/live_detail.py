import pendulum

from ..init_orator import Model

class LiveDetail(Model):
        
    def fresh_timestamp(self):
        return pendulum.now()
