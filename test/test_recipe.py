""" Test all things tied to recipes. """
from __future__ import absolute_import

import os
import pytest

from wok.recipe import *
from wok.conf import *

class TestRecipeDB(object):
    def setup(self):
        self.config = Config()
        self.rdb = RecipeDB(self.config)
        self.formulas = __file__
        for i in range(0, 2):
            self.formulas = os.path.dirname(self.formulas)
        self.formulas = os.path.join(self.formulas, 'formula')
        self.rdb.update_db(self.formulas)

    def test_available(self):
        assert self.rdb.available() == ['ag', 'vim']

    def test_has(self):
        assert self.rdb.has('ag')
        assert not self.rdb.has('aaaaa')

    def test_get_found(self):
        obj = self.rdb.get('ag')
        assert isinstance(obj, Recipe)
        assert obj.name() == 'ag'

    def test_get_not_found(self):
        with pytest.raises(RecipeNotFound):
            self.rdb.get('xyzxyz')

    def test_search(self):
        assert self.rdb.search('vm') == ['vim']
        assert self.rdb.search('zzzzyyy') == []
