""" Test configuration code. """
from __future__ import absolute_import, print_function

import mock
import os

from pakit.conf import Config, InstallDB, YamlMixin
from pakit.main import global_init
from pakit.recipe import RecipeDB


class TestYamlMixin(object):
    """ Specifically test mixin separate from targets. """
    def setup(self):
        self.config = YamlMixin('./test.yaml')

    def teardown(self):
        try:
            os.remove(self.config.filename)
        except OSError:
            pass

    def test_filename_get(self):
        assert self.config.filename == './test.yaml'

    @mock.patch('pakit.conf.logging')
    def test_filename_set(self, mock_log):
        expect = './not_test.yaml'
        self.config.filename = expect
        mock_log.error.assert_called_with('File not found: %s', expect)
        assert self.config.filename == expect

    def test_read_from(self):
        with open(self.config.filename, 'w+b') as fout:
            fout.write('hello: world\n'.encode())
        obj = self.config.read_from()
        assert type(obj) == type({})
        assert obj['hello'] == 'world'

    def test_write_to(self):
        self.config.write_to({'hello': 'world'})
        assert os.path.exists(self.config.filename)
        with open(self.config.filename) as fin:
            assert fin.readlines() == ['hello: world\n']


class TestConfig(object):
    """ Test the operation of Config class. """
    def setup(self):
        self.config = Config('./pakit.yaml')

    def teardown(self):
        try:
            os.remove(self.config.filename)
        except OSError:
            pass

    def test_get(self):
        assert self.config.get('paths.prefix') == '/tmp/pakit/builds'

    def test_get_opts(self):
        """ Requires the testing pakit.yaml. """
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
        config = Config(config_file)
        opts = config.get_opts('ag')
        assert opts.get('repo') == 'unstable'
        assert opts.get('prefix') == '/tmp/test_pakit/builds'

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

    def test_reset(self):
        self.config.set('paths.prefix', 22)
        self.config.reset()
        assert self.config.get('paths.prefix') == '/tmp/pakit/builds'

    def test__str__(self):
        print()
        print(str(self.config))
        expect = [
            'Config File: {0}'.format(self.config.filename),
            'Contents:',
            '{',
            '  "defaults": {',
            '    "repo": "stable"',
            '  },',
            '  "log": {',
            '    "enabled": true,',
            '    "file": "/tmp/pakit/main.log"',
            '  },',
            '  "paths": {',
            '    "link": "/tmp/pakit/links",',
            '    "prefix": "/tmp/pakit/builds",',
            '    "source": "/tmp/pakit/src"',
            '  }',
            '}',
        ]
        assert str(self.config).split('\n') == expect

class TestInstalledConfig(object):
    def setup(self):
        global_init(os.path.join(os.path.dirname(__file__), 'pakit.yaml'))
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
            '    "hash": "c81622c5c5313c05eab2da3b5eca6c118b74369e",',
            '    "repo": "stable",',
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
