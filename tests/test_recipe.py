"""
Test pakit.recipe
"""
from __future__ import absolute_import, print_function
import os
import sys
import copy
import mock
import pytest

from pakit.exc import PakitError
import pakit.recipe
from pakit.recipe import (
    Recipe, RecipeDB, RecipeDecorator, RecipeManager, check_package
)
import tests.common as tc


class TestCheckPackage(object):
    def setup(self):
        self.test_module = os.path.join(tc.STAGING, 'module')

    def teardown(self):
        tc.delete_it(self.test_module)

    def test_check_package_bad_name(self):
        self.test_module = os.path.join(tc.STAGING, '.module')
        os.makedirs(self.test_module)
        with pytest.raises(PakitError):
            check_package(self.test_module)

    def test_check_package_missing_init(self):
        init = os.path.join(self.test_module, '__init__.py')
        os.makedirs(self.test_module)
        assert not os.path.isfile(init)
        check_package(self.test_module)
        assert os.path.isfile(init)

    def test_check_package_non_existant(self):
        assert not os.path.exists(self.test_module)
        check_package(self.test_module)
        assert not os.path.exists(self.test_module)


class DummyRecipe(object):
    def __init__(self):
        self.msgs = []
        self.orig_dir = os.getcwd()

    def build(self, *args, **kwargs):
        self.msgs.append('build')

    def post_build(self):
        self.msgs.append('post_build')
        assert os.getcwd() == self.orig_dir

    def pre_build(self):
        self.msgs.append('pre_build')

    def verify(self, *args, **kwargs):
        assert os.getcwd().find('pakit_verify_') != -1


def test_decorator_pre_and_post():
    DummyRecipe.build = RecipeDecorator()(DummyRecipe.build)
    dummy = DummyRecipe()
    dummy.build()
    assert dummy.msgs == ['pre_build', 'build', 'post_build']


def test_decorator_tempd():
    DummyRecipe.verify = RecipeDecorator(use_tempd=True)(DummyRecipe.verify)
    dummy = DummyRecipe()
    dummy.verify()


class TestRecipe(object):
    def setup(self):
        self.config = tc.CONF
        self.recipe = pakit.recipe.RDB.get('ag')

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
            '  Requires: ',
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
            '  Requires: ',
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
        self.recipe.install_dir == self.config.path_to('prefix')

    def test_link_dir(self):
        self.recipe.link_dir == self.config.path_to('link')

    def test_source_dir(self):
        self.recipe.source_dir == self.config.path_to('source')

    def test_repo_get(self):
        self.recipe.repo == 'stable'

    def test_repo_set(self):
        with pytest.raises(KeyError):
            self.recipe.repo = 'aaaaa'

    def test_cmd_str(self):
        cmd = self.recipe.cmd('echo {prefix}')
        expect = [os.path.join(self.config.path_to('prefix'), 'ag')]
        assert cmd.output() == expect

    def test_cmd_list(self):
        cmd = self.recipe.cmd('echo {prefix}'.split())
        expect = [os.path.join(self.config.path_to('prefix'), 'ag')]
        assert cmd.output() == expect

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
                tc.delete_it(test_dir)
            except OSError:
                pass

    @mock.patch('pakit.shell.Command.wait')
    def test_cmd_timeout_arg(self, mock_cmd):
        self.recipe.cmd('ls', timeout=1)
        mock_cmd.assert_called_with(1)


class TestRecipeDB(object):
    def test__contains__(self):
        assert 'ag' in pakit.recipe.RDB
        assert 'aaaa' not in pakit.recipe.RDB

    def test__iter__(self):
        actual = sorted([key for key, _ in pakit.recipe.RDB])
        assert len(actual) != 0
        assert 'ag' in actual

    def test_get_found(self):
        obj = pakit.recipe.RDB.get('ag')
        assert isinstance(obj, Recipe)
        assert obj.name == 'ag'

    def test_get_not_found(self):
        with pytest.raises(PakitError):
            pakit.recipe.RDB.get('xyzxyz')

    def test_names(self):
        for prog in ['ag', 'vim']:
            assert prog in pakit.recipe.RDB.names()

    def test_index(self):
        test_uri = tc.CONF.get('pakit.recipe.uris')[1]['uri']
        recipe_base = os.path.basename(test_uri)
        test_recipes = os.path.join(tc.CONF.path_to('recipes'), recipe_base)
        rdb = RecipeDB(tc.CONF)
        rdb.index(test_recipes)
        assert 'cyclea' in rdb

    def test_recipe_obj(self):
        recipes_path = os.path.join(tc.CONF.path_to('recipes'), 'test_recipes')
        try:
            sys.path.insert(0, os.path.dirname(recipes_path))
            recipe = pakit.recipe.RDB.recipe_obj('base_recipes', 'ag')
            assert isinstance(recipe, Recipe)
            assert recipe.name == 'ag'
        finally:
            if recipes_path in sys.path:
                sys.path.remove(recipes_path)


class TestRecipeManager(object):
    def setup(self):
        self.git_uri = os.path.join(tc.STAGING, 'git')
        self.config = copy.deepcopy(tc.CONF)
        self.config.set('pakit.recipe.uris', [{'uri': self.git_uri}])
        self.config.set('pakit.paths.recipes',
                        os.path.join(tc.STAGING, 'test_recipes'))
        self.manager = None

    def teardown(self):
        if self.manager:
            tc.delete_it(self.manager.uri_db.filename)
        tc.delete_it(self.config.path_to('recipes'))
        os.makedirs(self.config.path_to('recipes'))

    def test_init_new_uris_vcs(self):
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        expect = os.path.join(self.config.path_to('recipes'),
                              self.manager.uri_db[self.git_uri]['path'],
                              '.git')
        assert os.path.exists(expect)

    def test_init_new_uris_vcs_unsupported(self):
        self.config.set('pakit.recipe.uris',
                        [{'uri': 'https://www.google.ca'}])
        self.manager = RecipeManager(self.config)
        with pytest.raises(PakitError):
            self.manager.init_new_uris()

    def test_init_new_uris_vcs_kwargs(self):
        uri = {'tag': '0.31.0', 'uri': self.git_uri}
        self.config.set('pakit.recipe.uris', [uri])
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        expect = os.path.join(self.config.path_to('recipes'),
                              self.manager.uri_db[self.git_uri]['path'],
                              '.git')
        assert os.path.exists(expect)

    def test_init_new_uris_local_path(self):
        uri = 'user_recipes'
        expect = os.path.join(self.config.path_to('recipes'), uri)
        self.config.set('pakit.recipe.uris', [{'uri': uri}])
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        assert os.path.exists(expect)

    def test_init_new_uris_local_path_exists(self):
        uri = 'user_recipes'
        expect = os.path.join(self.config.path_to('recipes'), uri)
        os.makedirs(expect)
        self.config.set('pakit.recipe.uris', [{'uri': uri}])
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        assert os.path.exists(expect)

    def test_paths(self):
        uri = 'user_recipes'
        expect = [os.path.join(self.config.path_to('recipes'), uri)]
        self.config.set('pakit.recipe.uris', [{'uri': uri}])
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        assert self.manager.paths == expect

    def test_check_for_deletions(self):
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()

        path = os.path.join(self.config.path_to('recipes'),
                            self.manager.uri_db[self.git_uri]['path'])
        tc.delete_it(path)
        assert not os.path.exists(path)
        assert self.git_uri in self.manager.uri_db
        self.manager.check_for_deletions()
        assert self.git_uri not in self.manager.uri_db

    def test_check_for_updates_interval(self):
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        interval = self.config.get('pakit.recipe.update_interval')
        old_time = self.manager.uri_db[self.git_uri]['time'] - 2 * interval
        self.manager.uri_db[self.git_uri]['time'] = old_time
        self.manager.uri_db.write()

        self.manager.check_for_updates()
        assert self.manager.uri_db[self.git_uri]['time'] != old_time

    def test_check_for_updates_kwargs(self):
        self.manager = RecipeManager(self.config)
        self.manager.init_new_uris()
        uri = {'tag': '0.31.0', 'uri': self.git_uri}
        self.config.set('pakit.recipe.uris', [uri])
        self.manager = RecipeManager(self.config)

        old_time = self.manager.uri_db[self.git_uri]['time']
        self.manager.check_for_updates()
        assert self.manager.uri_db[self.git_uri]['time'] != old_time
