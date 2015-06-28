""" Test configuration code. """
from __future__ import absolute_import

import os
import yaml

from wok.conf import Config, TEMPLATE

WOK_FILE = './wok.yaml'

class TestConfig(object):
    def setup(self):
        output = yaml.dump(TEMPLATE)
        with open(WOK_FILE, 'w') as fout:
            fout.write(output)

        self.co = Config(WOK_FILE)

    def teardown(self):
        os.remove(WOK_FILE)

    def test_get(self):
        assert self.co.paths.get('prefix') == '/tmp/wok/builds'

    def test_filename(self):
        wok2 = './wok2.yaml'
        self.co.filename = wok2
        self.co.write()
        assert os.path.exists(wok2)
        os.remove(wok2)

    def test_set(self):
        self.co.set('paths.prefix', '/dev/null')
        assert self.co.paths.get('prefix') == '/dev/null'

    def test_write(self):
        self.co.set('paths.install', 22)
        self.co.write()
        self.co.load()
        assert self.co.paths.get('install') == 22

