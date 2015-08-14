""" Test configuration code. """
from __future__ import absolute_import, print_function

import os

from wok.conf import Config, InstallDB
from wok.main import global_init
from wok.recipe import RecipeDB

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

    def test_get_opts(self):
        """ Requires the testing wok.yaml. """
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        config = Config(config_file)
        opts = config.get_opts('ag')
        assert opts.get('repo') == 'unstable'
        assert opts.get('prefix') == '/tmp/test_wok/builds'

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

    def test__str__(self):
        print()
        print(str(self.config))
        expect = [
            'Config File: {0}'.format(self.config.filename),
            'Contents:',
            '{',
            '  "defaults": {',
            '    "repo": "stable"',
            '  }, ',
            '  "log": {',
            '    "enabled": true, ',
            '    "file": "/tmp/wok/main.log"',
            '  }, ',
            '  "paths": {',
            '    "link": "/tmp/wok/links", ',
            '    "prefix": "/tmp/wok/builds", ',
            '    "source": "/tmp/wok/src"',
            '  }',
            '}',
        ]
        assert str(self.config).split('\n') == expect

class TestInstalledConfig(object):
    def setup(self):
        global_init(os.path.join(os.path.dirname(__file__), 'wok.yaml'))
        self.fname = './installed.yaml'
        self.config = InstallDB(self.fname)
        self.recipe = RecipeDB().get('ag')
        self.recipe.repo = 'stable'

    def teardown(self):
        try:
            os.remove(self.fname)
        except OSError:
            pass
        self.recipe.repo = 'unstable'

    def test__str__(self):
        expect = [
            'Config File: ./installed.yaml',
            'Contents:',
            '{',
            '  "ag": {',
            '    "hash": "c81622c5c5313c05eab2da3b5eca6c118b74369e", ',
            '    "repo": "stable", ',
            '  }',
            '}'
        ]
        self.config.add(self.recipe)
        print(str(self.config))
        lines = str(self.config).split('\n')
        del lines[7]
        del lines[4]
        assert expect == lines

    def test_add(self):
        self.config.add(self.recipe)
        ag = self.config.get('ag')
        assert ag['hash'] == self.recipe.repo.cur_hash

    def test_get(self):
        self.config.add(self.recipe)
        assert self.config.get('ag') is not None
        assert self.config.get('ag')['hash'] == self.recipe.repo.cur_hash
        self.config.remove('ag')
        assert self.config.get('ag') is None

    def test_remove(self):
        self.config.add(self.recipe)
        self.config.remove('ag')
        assert self.config.get('ag') is None

    def test_write(self):
        self.config.add(self.recipe)
        self.config.write()
        assert os.path.exists(self.config.filename)

    def test_read(self):
        self.config.add(self.recipe)
        self.config.write()
        self.config = InstallDB(self.fname)
        self.config.read()
        entry = self.config.get('ag')
        assert entry is not None
        assert entry['hash'] == self.recipe.repo.cur_hash
