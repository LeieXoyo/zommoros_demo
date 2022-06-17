from orator.orm import has_many
import pendulum

from ..init_orator import Model, db
from .test_info import TestInfo
from .live_info import LiveInfo
from .hist import Hist

class RunList(Model):

    __fillable__ = ['dataname', 'datetime', 'type']

    @has_many
    def test_infos(self):
        return TestInfo

    @has_many
    def live_infos(self):
        return LiveInfo

    @has_many
    def hists(self):
        return Hist

    def save_starting_value(self, starting_value):
        self.starting_value = starting_value
        db.reconnect(self.get_connection_name())
        self.save()

    def save_error(self, error):
        self.error = error
        db.reconnect(self.get_connection_name())
        self.save()

    def fresh_timestamp(self):
        return pendulum.now()
