""" Test all things tied to recipes. """
from __future__ import absolute_import, print_function

import os
import pytest

from wok.conf import *
from wok.main import global_init
from wok.recipe import *

class TestRecipeDB(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.rdb = RecipeDB()

    def test_names(self):
        for prog in ['ag', 'vim']:
            assert prog in self.rdb.names()

    def test_has(self):
        assert self.rdb.has('ag')
        assert not self.rdb.has('aaaaa')

    def test_get_found(self):
        obj = self.rdb.get('ag')
        assert isinstance(obj, Recipe)
        assert obj.name == 'ag'

    def test_get_not_found(self):
        with pytest.raises(RecipeNotFound):
            self.rdb.get('xyzxyz')

class TestRecipe(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.recipe = RecipeDB().get('ag')

    def test_with_func(self):
        with self.recipe:
            assert os.path.exists(self.recipe.source_dir)
            assert len(os.listdir(self.recipe.source_dir)) != 0

    def test_str(self):
        print()
        print(self.recipe)

        assert str(self.recipe) == 'ag: Grep like tool optimized for speed'

    def test_info(self):
        print()
        print(self.recipe.info())

        expect = [
                'ag: Grep like tool optimized for speed',
                '  Homepage: https://github.com/ggreer/the_silver_searcher',
                '  Stable Build:',
                '    Git: tag: 0.30.0, uri: https://github.com/ggreer/the_silver_searcher',
                '  Unstable Build:',
                '    Git: branch: HEAD, uri: https://github.com/ggreer/the_silver_searcher'
        ]

        assert self.recipe.info().split('\n') == expect
