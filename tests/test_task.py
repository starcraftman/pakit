""" All tests related to tasks. """
from __future__ import absolute_import

import glob
import logging
import mock
import os
import pytest

from wok.main import global_init
from wok.recipe import RecipeDB
from wok.shell import Command, CmdFailed
from wok.task import (
    subseq_match, substring_match, walk_and_link, walk_and_unlink,
    Task, RecipeTask, InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask
)
import wok.task

def teardown_module(module):
    try:
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        config = global_init(config_file)
        tmp_dir = os.path.dirname(config.get('paths.prefix'))
        cmd = Command('rm -rf ' + tmp_dir)
        cmd.wait()
    except CmdFailed:
        logging.error('Could not clean ' + tmp_dir)

def test_subseq_match():
    haystack = 'Hello World!'
    assert subseq_match(haystack, 'hwor')
    assert subseq_match(haystack, 'HeWd')
    assert not subseq_match(haystack, 'Good')

def test_substring_match():
    haystack = 'Hello World!'
    assert substring_match(haystack, 'hello')
    assert substring_match(haystack, 'Hello')
    assert not substring_match(haystack, 'HelloW')

class TestLinking(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        config = global_init(config_file)
        self.src = config.get('paths.prefix')
        self.dst = config.get('paths.link')
        self.teardown()

        self.subdir = os.path.join(self.src, 'subdir')
        os.makedirs(self.subdir)
        os.makedirs(self.dst)

        self.fnames = [os.path.join(self.src, 'file' + str(num)) for num in range(0, 6)]
        self.fnames += [os.path.join(self.subdir, 'file' + str(num)) for num in range(0, 4)]
        self.dst_fnames = [fname.replace(self.src, self.dst) for fname in self.fnames]
        for fname in self.fnames:
            with open(fname, 'wb') as fout:
                fout.write('dummy')

    def teardown(self):
        try:
            cmd = Command('rm -rf ' + os.path.dirname(self.src))
            cmd.wait()
        except CmdFailed:
            logging.error('Could not clean ' + self.src)

    def test_walk_and_link_works(self):
        walk_and_link(self.src, self.dst)
        for fname in self.dst_fnames:
            assert os.path.islink(fname)
            assert os.readlink(fname) == fname.replace(self.dst, self.src)

    def test_walk_and_link_raises(self):
        walk_and_link(self.src, self.dst)
        with pytest.raises(OSError):
            walk_and_link(self.src, self.dst)

    def test_walk_and_unlink(self):
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)

class TestTaskBase(object):
    """ Shared setup, most task tests will want this. """
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.rdb = RecipeDB()
        self.recipe = self.rdb.get('ag')

    def teardown(self):
        RemoveTask(self.recipe.name).run()

class TestTaskRecipe(TestTaskBase):
    def test_recipe(self):
        assert RecipeTask(self.recipe.name).recipe is self.recipe

    def test__eq__(self):
        assert InstallTask('ag') == InstallTask('ag')
        assert RemoveTask('ag') != InstallTask('ag')
        assert InstallTask('ag') != InstallTask('vim')

    def test__str__(self):
        expect = 'RecipeTask: ag           Grep like tool optimized for speed'
        task = RecipeTask(self.recipe.name)
        print(task)
        assert expect == str(task)

class TestTaskInstall(TestTaskBase):
    def test_is_not_installed(self):
        task = InstallTask(self.recipe.name)
        task.run()
        name = self.recipe.name
        build_bin = os.path.join(task.path('prefix'), name, 'bin', name)
        link_bin = os.path.join(task.path('link'), 'bin', name)
        assert os.path.exists(build_bin)
        assert os.path.exists(link_bin)
        assert os.path.realpath(link_bin) == build_bin

    @mock.patch('wok.task.logging')
    def test_is_installed(self, mock_log):
        task = InstallTask(self.recipe.name)
        task.run()
        task.run()
        assert mock_log.error.called is True

class TestTaskRemove(TestTaskBase):
    @mock.patch('wok.task.logging')
    def test_is_not_installed(self, mock_log):
        task = RemoveTask(self.recipe.name)
        task.run()
        mock_log.error.assert_called_with('Not Installed: ag')

    def test_is_installed(self):
        InstallTask(self.recipe.name).run()
        task = RemoveTask(self.recipe.name)
        task.run()

        assert os.path.exists(task.path('prefix'))
        globbed = glob.glob(os.path.join(task.path('prefix'), '*'))
        assert globbed == [os.path.join(task.path('prefix'), 'installed.yaml')]
        assert not os.path.exists(task.path('link'))

class TestTaskUpdate(TestTaskBase):
    def test_is_current(self):
        recipe = self.recipe
        InstallTask(recipe.name).run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash
        first_hash = recipe.repo.cur_hash

        UpdateTask(recipe.name).run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash
        assert first_hash == recipe.repo.cur_hash

    def test_is_not_current(self):
        recipe = self.recipe
        old_repo_name = recipe.repo_name

        recipe.repo = 'stable'
        InstallTask(recipe.name).run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash

        recipe.repo = 'unstable'
        UpdateTask(recipe.name).run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash

        recipe.repo = old_repo_name

class TestTaskQuery(TestTaskBase):
    def test_list_installed(self):
        InstallTask(self.recipe.name).run()
        task = ListInstalled()
        out = task.run().split('\n')
        assert len(out) == 3
        assert out[-1].find('  ' + self.recipe.name) == 0

    def test_list_available(self):
        task = ListAvailable()
        out = task.run().split('\n')
        expect = ['  ' + line for line in RecipeDB().names_and_desc()]
        print(expect)
        print(out)
        assert out[0] == 'Available Recipes:'
        assert out[2:] == expect

    def test_search_names(self):
        results = SearchTask('vim', RecipeDB().names()).run()
        assert results == ['vim']

    def test_search_desc(self):
        results = SearchTask('grep', RecipeDB().names_and_desc()).run()
        assert results == [str(self.recipe)]

    def test_display_info(self):
        results = DisplayTask(self.recipe.name).run()
        assert results == self.recipe.info()
