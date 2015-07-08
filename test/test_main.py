""" Test main functionality. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.main import *
from wok.conf import Config

@pytest.fixture(scope='module')
def clean_up(request):
    """ Ensure clean test area. """
    try:
        shutil.rmtree(request.paths.get('prefix'))
    except OSError:
        pass
    try:
        shutil.rmtree(request.paths.get('link'))
    except OSError:
        pass

class TestAction(object):
    def setup(self):
        self.config = Config()
        self.paths = self.config.paths

    def test_act_install(self):
        install = InstallAction(paths=self.paths, progs=['ag'])
        install()

        bin_installed = os.path.join(self.paths.get('prefix'), 'ag', 'bin', 'ag')
        bin_linked = os.path.join(self.paths.get('link'), 'bin', 'ag')
        assert os.path.exists(bin_installed)
        assert os.path.exists(bin_linked)

    def test_act_list(self):
        list = ListAction(paths=self.paths)
        assert list() == ['ag']

    def test_act_remove(self):
        rem = RemoveAction(paths=self.paths, progs=['ag'])
        rem()

        assert os.path.exists(self.paths.get('prefix'))
        assert len(glob.glob(os.path.join(
                self.paths.get('prefix'), '*'))) == 0
        assert os.path.exists(self.paths.get('link'))
        assert len(glob.glob(os.path.join(
                self.paths.get('link'), '*'))) == 0

    @pytest.mark.xfail
    def test_act_update(self):
        assert False
