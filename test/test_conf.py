""" Test configuration code. """
from __future__ import absolute_import

import os

from wok.conf import Config, InstalledConfig

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

    def test_str(self):
        print()
        print(str(self.config))
        expect = [
                'Config File: {0}'.format(self.config.filename),
                'Contents: ',
                '{',
                '  "log": {',
                '    "enabled": true, ',
                '    "file": "/tmp/wok/main.log"',
                '  }, ',
                '  "paths": {',
                '    "link": "/tmp/wok/links", ',
                '    "prefix": "/tmp/wok/builds", ',
                '    "source": "/tmp/wok/src"',
                '  }',
                '}'
        ]
        assert str(self.config).split('\n') == expect

class TestInstalledConfig(object):
    def setup(self):
        self.fname = './wok.in.yaml'
        self.config = InstalledConfig(self.fname)

    def teardown(self):
        try:
            os.remove(self.fname)
        except OSError:
            pass

    def test_add(self):
        self.config.add('ag', 'hello')
        ag = self.config.get('ag')
        assert ag['hash'] == 'hello'

    def test_get(self):
        self.config.add('ag', 'hello')
        assert self.config.get('ag') is not None
        assert self.config.get('ag')['hash'] == 'hello'
        self.config.remove('ag')
        assert self.config.get('ag') is None

    def test_remove(self):
        self.config.add('ag', 'hello')
        self.config.remove('ag')
        assert self.config.get('ag') is None

    def test_write(self):
        self.config.add('ag', 'hello')
        self.config.write()
        assert os.path.exists(self.config.filename)

    def test_read(self):
        self.config.add('ag', 'hello')
        self.config.write()
        self.config = InstalledConfig(self.fname)
        self.config.read()
        entry = self.config.get('ag')
        assert entry is not None
        assert entry['hash'] == 'hello'
