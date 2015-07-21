""" All tests related to tasks. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.conf import Config
from wok.recipe import RecipeDB
from wok.shell import Command, CmdFailed
from wok.task import *

def setup_module(module):
    config = Config()
    Task.set_config(config)
    for path in config.get('paths').values():
        try:
            shutil.rmtree(path)
            os.mkdir(path)
        except OSError:
            pass

def teardown_module(module):
    setup_module(module)
    os.rmdir('/tmp/woklink')

class TestLinking(object):
    def setup(self):
        self.src = '/tmp/woklink/src'
        self.dst = '/tmp/woklink/dst'
        self.teardown()

        subdir = os.path.join(self.src, 'subdir')
        os.makedirs(subdir)
        os.makedirs(self.dst)

        self.fnames = [os.path.join(self.src, 'file' + str(num)) for num in range(0, 6)]
        self.fnames += [os.path.join(subdir, 'file' + str(num)) for num in range(0, 4)]
        self.dst_fnames = [fname.replace(self.src, self.dst) for fname in self.fnames]
        for fname in self.fnames:
            with open(fname, 'wb') as fout:
                fout.write('dummy')

    def teardown(self):
        try:
            cmd = Command('rm -rf ' + self.src)
            cmd.wait()
        except CmdFailed:
            logging.error('Could not clean ' + self.src)
        try:
            cmd = Command('rm -rf ' + self.dst)
            cmd.wait()
        except CmdFailed:
            logging.error('Could not clean ' + self.dst)

    def test_walk_and_link(self):
        walk_and_link(self.src, self.dst)
        for fname in self.dst_fnames:
            assert os.path.islink(fname)
            assert os.readlink(fname) == fname.replace('dst', 'src')

    def test_walk_and_unlink(self):
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(os.path.join(self.dst, 'subdir'))
        for fname in self.fnames:
            assert os.path.exists(fname)

class TestTasks(object):
    def setup(self):
        self.config = Config()
        self.rdb = RecipeDB(self.config)

    def test_install(self):
        task = InstallTask('ag')
        task.do()
        assert os.path.exists(os.path.join(task.prefix, 'ag', 'bin', 'ag'))

    def test_list(self):
        task = ListInstalled()
        expect = 'The following programs are installed:'
        expect += '\n-  ag: Grep like tool optimized for speed'
        assert task.do() == expect


    @pytest.mark.xfail
    def test_search(self):
        pass

    @pytest.mark.xfail
    def test_update(self):
        pass

    def test_remove(self):
        task  = RemoveTask('ag')
        assert os.path.exists(os.path.join(task.prefix, 'ag'))

        task.do()

        assert os.path.exists(task.prefix)
        assert len(glob.glob(os.path.join(
                task.prefix, '*'))) == 0
        assert not os.path.exists(task.link)
        assert len(glob.glob(os.path.join(
                task.prefix, '*'))) == 0
