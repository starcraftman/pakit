""" All tests related to tasks. """
from __future__ import absolute_import

import glob
import logging
import os
import pytest
import shutil

from wok.conf import Config
from wok.recipe import RecipeDB
from wok.task import *

def setup_module(module):
    config = Config()
    Task.set_config(config)
    for path in config.paths.values():
        try:
            shutil.rmtree(path)
            os.mkdir(path)
        except OSError:
            pass

def teardown_module(module):
    setup_module(module)

class TestTasks(object):
    def setup(self):
        self.config = Config()
        self.rdb = RecipeDB(self.config)

    def test_install(self):
        task = InstallTask('ag')
        task.do()
        assert os.path.exists(os.path.join(task.prefix, 'ag', 'bin', 'ag'))

    def test_list(self):
        task = ListTask()
        assert task.do() == 'The following programs are installed:\n  - ag'

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
        assert os.path.exists(task.link)
        assert len(glob.glob(os.path.join(
                task.prefix, '*'))) == 0