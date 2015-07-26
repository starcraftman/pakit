""" Test all things tied to recipes. """
from __future__ import absolute_import, print_function

import os
import pytest

from wok.recipe import *
from wok.conf import *

class TestRecipeDB(object):
    def setup(self):
        self.config = Config()
        self.rdb = RecipeDB(self.config)

    def test_names(self):
        for prog in ['ag', 'vim']:
            assert prog in self.rdb.names()

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

class TestRecipe(object):
    def setup(self):
        self.recipe = RecipeDB(Config()).get('ag')

    def teardown(self):
        pass

    def test_str(self):
        print()
        print(self.recipe)

        assert str(self.recipe) == 'ag: Grep like tool optimized for speed'

    def test__info(self):
        print()
        print(self.recipe.info())

        expect = [
                'ag: Grep like tool optimized for speed',
                '  Homepage: https://github.com/ggreer/the_silver_searcher',
                '  Stable Build:',
                '    Git: tag: 0.30.0, uri: https://github.com/ggreer/the_silver_searcher',
                '  Unstable Build:',
                '    Git: branch: default, uri: https://github.com/ggreer/the_silver_searcher'
        ]

        assert self.recipe.info().split('\n') == expect
