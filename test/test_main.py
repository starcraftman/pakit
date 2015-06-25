""" Test main functionality. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.main import *
from wok.conf import Config

WOK_CONF = os.path.expanduser('~/.wok.yaml')

class TestAction(object):
    def setup(self):
        self.config = Config(WOK_CONF)
        self.config.load()

    def test_act_install(self):
        # One time ensure for now
        try:
            shutil.rmtree(self.config.install_to)
            shutil.rmtree(self.config.link_to)
        except OSError:
            pass

        inst = InstallAction(config=self.config, progs=['ag'])
        assert inst()

        bin_installed = os.path.join(self.config.install_to, 'ag', 'bin', 'ag')
        bin_linked = os.path.join(self.config.link_to, 'bin', 'ag')
        assert os.path.exists(bin_installed)
        assert os.path.exists(bin_linked)

    def test_act_list(self):
        list = ListAction(config=self.config)
        assert list() == ['ag']

    def test_act_remove(self):
        rem = RemoveAction(config=self.config, progs=['ag'])
        rem()

        assert os.path.exists(self.config.install_to)
        assert len(glob.glob(os.path.join(
                self.config.install_to, '*'))) == 0
        assert os.path.exists(self.config.link_to)
        assert len(glob.glob(os.path.join(
                self.config.link_to, '*'))) == 0

    @pytest.mark.xfail
    def test_act_update(self):
        assert False
