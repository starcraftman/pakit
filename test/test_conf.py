""" Test configuration code. """
from __future__ import absolute_import

import os

from wok.conf import Config

WOK_FILE = './wok.yaml'
TEMPLATE = """\
install_to: /tmp/wok/builds
link_to: /tmp/wok/links
log_on: true
log_to: /tmp/wok/main.log,
"""

class TestConfig(object):
    def setup(self):
        with open(WOK_FILE, 'w') as fout:
            fout.write(TEMPLATE)

    def teardown(self):
        os.remove(WOK_FILE)

    def test_get(self):
        co = Config(WOK_FILE)
        assert co.install_to == '/tmp/wok/builds'

    def test_write(self):
        co = Config(WOK_FILE)
        co.set('install_to', 22)
        co.write()
        co.load()
        assert co.install_to == 22
