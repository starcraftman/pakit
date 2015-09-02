"""
Test pakit.recipe
"""
from __future__ import absolute_import, print_function

import os
import pytest

from pakit.exc import PakitError
from pakit.recipe import Recipe, RecipeDB
import tests.common as tc


class TestRecipe(object):
    def setup(self):
        self.config = tc.env_setup()
        self.recipe = RecipeDB().get('ag')

    def test_repo_set_fail(self):
        with pytest.raises(KeyError):
            self.recipe.repo = 'hello'

    def test_with_func(self):
        with self.recipe:
            assert os.path.exists(self.recipe.source_dir)
            assert len(os.listdir(self.recipe.source_dir)) != 0
            expect = self.recipe.repos.get('unstable').src_hash
            assert self.recipe.repo.src_hash == expect

    def test__str__(self):
        print()
        print(self.recipe)
        expect = 'ag           Grep like tool optimized for speed'
        assert str(self.recipe) == expect

    def test_info(self):
        print()
        print(self.recipe.info())
        uri = self.recipe.repo.uri
        expect = [
            'ag',
            '  Description: Grep like tool optimized for speed',
            '  Homepage: ' + uri,
            '  Current Repo: "unstable"',
            '  Repo "stable":',
            '    Git: tag: 0.30.0, uri: ' + uri,
            '  Repo "unstable":',
            '    Git: branch: master, uri: ' + uri,
        ]
        assert self.recipe.info().split('\n') == expect

    def test_repo_set(self):
        with pytest.raises(KeyError):
            self.recipe.repo = 'aaaaa'


class TestRecipeDB(object):
    def setup(self):
        self.config = tc.env_setup()

    def test_names(self):
        for prog in ['ag', 'vim']:
            assert prog in RecipeDB().names()

    def test__contains__(self):
        assert 'ag' in RecipeDB()
        assert 'aaaa' not in RecipeDB()

    def test_get_found(self):
        obj = RecipeDB().get('ag')
        assert isinstance(obj, Recipe)
        assert obj.name == 'ag'

    def test_get_not_found(self):
        with pytest.raises(PakitError):
            RecipeDB().get('xyzxyz')
