""" Test configuration code. """
from __future__ import absolute_import

import os

from wok.conf import Config

class TestConfig(object):
    """ Test the operation of Config class. """
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

    def test_get(self):
        assert self.config.get('paths.prefix') == '/tmp/wok/builds'

    def test_set(self):
        self.config.set('paths.prefix', '/dev/null')
        assert self.config.get('paths.prefix') == '/dev/null'

        self.config.set('hello.world', True)
        assert self.config.get('hello.world') is True

    def test_write(self):
        self.config.set('paths.install', 22)
        self.config.write()
        self.config.read()
        assert self.config.get('paths.install') == 22

