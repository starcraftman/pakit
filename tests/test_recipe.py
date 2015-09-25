"""
Test pakit.recipe
"""
from __future__ import absolute_import, print_function

import os
import pytest
import shutil

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
            '    Git: tag: 0.31.0, uri: ' + uri,
            '  Repo "unstable":',
            '    Git: branch: master, uri: ' + uri,
        ]
        assert self.recipe.info().split('\n') == expect

    def test_info_strip_spaces(self):
        print()
        self.recipe.__doc__ = """
        Grep like tool optimized for speed


        Start of new text.

        Second paragraph.

        """
        print(self.recipe.info())
        uri = self.recipe.repo.uri
        expect = [
            'ag',
            '  Description: Grep like tool optimized for speed',
            '  Homepage: ' + uri,
            '  Current Repo: "unstable"',
            '  Repo "stable":',
            '    Git: tag: 0.31.0, uri: ' + uri,
            '  Repo "unstable":',
            '    Git: branch: master, uri: ' + uri,
            '  More Information:',
            '    Start of new text.',
            '    ',
            '    Second paragraph.',
        ]
        assert self.recipe.info().split('\n') == expect

    def test_install_dir(self):
        self.recipe.install_dir == self.config.get('pakit.paths.prefix')

    def test_link_dir(self):
        self.recipe.link_dir == self.config.get('pakit.paths.link')

    def test_source_dir(self):
        self.recipe.source_dir == self.config.get('pakit.paths.source')

    def test_repo_get(self):
        self.recipe.repo == 'stable'

    def test_repo_set(self):
        with pytest.raises(KeyError):
            self.recipe.repo = 'aaaaa'

    def test_cmd_str(self):
        cmd = self.recipe.cmd('echo {prefix}')
        expect = [os.path.join(self.config.get('pakit.paths.prefix'), 'ag')]
        assert cmd.output() == expect

    def test_cmd_list(self):
        cmd = self.recipe.cmd('echo {prefix}'.split())
        expect = [os.path.join(self.config.get('pakit.paths.prefix'), 'ag')]
        assert cmd.output() == expect

    def test_cmd_dir_default(self):
        test_dir = '/tmp'
        self.recipe.def_cmd_dir = test_dir
        cmd = self.recipe.cmd('pwd')
        assert cmd.output() == [test_dir]

    def test_cmd_dir_arg(self):
        try:
            test_dir = os.path.join('/tmp', 'pakit_folder')
            try:
                os.makedirs(test_dir)
            except OSError:
                pass
            cmd = self.recipe.cmd('pwd', cmd_dir=test_dir)
            assert cmd.output() == [test_dir]
        finally:
            try:
                shutil.rmtree(test_dir)
            except OSError:
                pass


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
