""" Test main functionality. """
from __future__ import absolute_import

import glob
import os
import pytest
import shutil

from wok.main import *
from wok.conf import Config

WOK_CONF = os.path.expanduser('~/wok.yaml')

class TestAction(object):
    def setup(self):
        self.config = Config(WOK_CONF)
        self.config.load()
        try:
            shutil.rmtree(self.config.install_to)
            shutil.rmtree(self.config.link_to)
        except OSError:
            pass

    def test_act_install(self):
        inst = InstallAction(config=self.config, progs=['ags'])
        inst()

        bin_installed = os.path.join(self.config.install_to, 'ag', 'bin', 'ag')
        bin_linked = os.path.join(self.config.link_to, 'bin', 'ag')
        assert os.path.exists(bin_installed)
        assert os.path.exists(bin_linked)

    @pytest.mark.xfail
    def test_act_list(self):
        assert False

    def test_act_remove(self):
        rem = RemoveAction(config=self.config, progs=['ag'])
        rem()

        assert not os.path.exists(self.config.install_to)
        assert not os.path.exists(self.config.link_to)

    @pytest.mark.xfail
    def test_act_update(self):
        assert False
