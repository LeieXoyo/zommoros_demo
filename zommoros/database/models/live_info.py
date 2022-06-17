from orator.orm import has_many
import pendulum

from ..init_orator import Model
from .live_detail import LiveDetail

class LiveInfo(Model):

    __fillable__ = ['run_list_id']
    
    @has_many
    def details(self):
        return LiveDetail

    def fresh_timestamp(self):
        return pendulum.now()
