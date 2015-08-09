""" All tests related to tasks. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.conf import Config
from wok.main import global_init
from wok.recipe import RecipeDB
from wok.shell import Command, CmdFailed, Git
from wok.task import *
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

    def test_walk_and_link(self):
        walk_and_link(self.src, self.dst)
        for fname in self.dst_fnames:
            assert os.path.islink(fname)
            assert os.readlink(fname) == fname.replace(self.dst, self.src)

    def test_walk_and_unlink(self):
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)

class TestTasks(object):
    """ These depend on order, so no cleanup in between. """
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.rdb = RecipeDB()

    def teardown(self):
        wok.task.IDB.write()

    def test__eq__(self):
        assert InstallTask('ag') == InstallTask('ag')
        assert RemoveTask('ag') != InstallTask('ag')

    def test_install(self):
        task = InstallTask('ag')
        task.run()
        assert os.path.exists(os.path.join(task.path('prefix'), 'ag', 'bin', 'ag'))

    def test_list(self):
        task = ListInstalled()
        out = task.run().split('\n')
        assert len(out) == 3
        assert out[-1].find('-  ag') == 0

    def test_search_names(self):
        results = SearchTask('vim', RecipeDB().names()).run()
        assert results == ['vim']

    def test_search_desc(self):
        results = SearchTask('grep', RecipeDB().names_and_desc()).run()
        assert results == ['ag: Grep like tool optimized for speed']

    def test_remove(self):
        task = RemoveTask('ag')
        assert os.path.exists(os.path.join(task.path('prefix'), 'ag'))
        assert wok.task.IDB.get('ag') is not None

        task.run()
        assert os.path.exists(task.path('prefix'))
        assert len(glob.glob(os.path.join(
                task.path('prefix'), '*'))) == 1
        assert not os.path.exists(task.path('link'))
        assert len(glob.glob(os.path.join(
                task.path('link'), '*'))) == 0

    def test_update(self):
        """ Builds stable, then updates because unstable is newer. """
        recipe = self.rdb.get('ag')

        # Manually install stable version for now
        recipe.repo = 'stable'
        InstallTask('ag').run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash

        recipe.repo = 'unstable'
        UpdateTask('ag').run()
        assert wok.task.IDB.get(recipe.name)['hash'] == recipe.repo.cur_hash
        del recipe
