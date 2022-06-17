from orator.orm import has_many
import pendulum

from ..init_orator import Model
from .test_detail import TestDetail

class TestInfo(Model):

    __fillable__ = ['run_list_id']

    @has_many
    def details(self):
        return TestDetail

    def fresh_timestamp(self):
        return pendulum.now()
