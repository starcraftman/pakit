""" All tests related to tasks. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.conf import Config
from wok.main import global_init
from wok.recipe import RecipeDB
from wok.shell import Command, CmdFailed
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

    def test_install(self):
        task = InstallTask('ag')
        task.do()
        assert os.path.exists(os.path.join(task.prefix, 'ag', 'bin', 'ag'))

    def test_list(self):
        task = ListInstalled()
        expect = 'The following programs are installed:'
        expect += '\n-  ag: Grep like tool optimized for speed'
        assert task.do() == expect

    def test_search_names(self):
        results = SearchTask('vim', RecipeDB().names()).do()
        assert results == ['vim']

    def test_search_desc(self):
        results = SearchTask('grep', RecipeDB().names_and_desc()).do()
        assert results == ['ag: Grep like tool optimized for speed']

    @pytest.mark.xfail
    def test_update(self):
        pass

    def test_remove(self):
        task = RemoveTask('ag')
        assert os.path.exists(os.path.join(task.prefix, 'ag'))
        assert wok.task.IDB.get('ag') is not None

        task.do()
        assert os.path.exists(task.prefix)
        assert len(glob.glob(os.path.join(
                task.prefix, '*'))) == 0
        assert not os.path.exists(task.link)
        assert len(glob.glob(os.path.join(
                task.prefix, '*'))) == 0
