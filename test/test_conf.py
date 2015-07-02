""" Test configuration code. """
from __future__ import absolute_import

import os
import yaml

from wok.conf import Config

class TestConfig(object):
    def setup(self):
        self.config = Config('./wok.yaml')

    def teardown(self):
        try:
            os.remove(self.config.filename)
        except OSError:
            pass

    def test_filename(self):
        self.config.write()
        assert os.path.exists(self.config.filename)
        os.remove(self.config.filename)

    def test_get(self):
        assert self.config.paths.get('prefix') == '/tmp/wok/builds'

    def test_set(self):
        self.config.set('paths.prefix', '/dev/null')
        assert self.config.paths.get('prefix') == '/dev/null'

    def test_write(self):
        self.config.set('paths.install', 22)
        self.config.write()
        self.config.load()
        assert self.config.paths.get('install') == 22

