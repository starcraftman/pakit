"""
Test pakit.conf
"""
from __future__ import absolute_import, print_function

import mock
import os
import pytest
import subprocess as sub

import pakit.conf
import pakit.recipe
from pakit.conf import Config, InstallDB, YamlMixin, RecipeURIDB
import tests.common as tc


class TestYamlMixin(object):
    """ Specifically test mixin separate from targets. """
    def setup(self):
        self.config_file = os.path.join(tc.STAGING, 'file.yaml')
        self.config = YamlMixin(self.config_file)

    def teardown(self):
        tc.delete_it(self.config_file)

    def test_filename_get(self):
        assert self.config.filename == self.config_file

    @mock.patch('pakit.conf.logging')
    def test_filename_set(self, mock_log):
        new_file = self.config_file + '2'
        self.config.filename = new_file
        mock_log.error.assert_called_with('File not found: %s', new_file)
        assert self.config.filename == new_file

    def test_read_from(self):
        with open(self.config.filename, 'wb') as fout:
            fout.write('hello: world\n'.encode())
        obj = self.config.read_from()
        assert isinstance(obj, dict)
        assert obj['hello'] == 'world'

    @mock.patch('pakit.conf.logging')
    def test_read_from_file_invalid(self, mock_log):
        assert not os.path.exists(self.config.filename)
        self.config.read_from()
        assert mock_log.error.called

    def test_write_to(self):
        self.config.write_to({'hello': 'world'})
        assert os.path.exists(self.config.filename)
        with open(self.config.filename) as fin:
            assert fin.readlines() == ['hello: world\n']


class TestConfig(object):
    """ Test the operation of Config class. """
    def setup(self):
        self.config_file = os.path.join(tc.STAGING, 'pakit.yml')
        self.config = Config(self.config_file)

    def teardown(self):
        tc.delete_it(self.config_file)

    def test__str__(self):
        print()
        print(str(self.config))
        expect = """Config File: PLACE0
Contents:
{
  "pakit": {
    "command": {
      "timeout": 120
    },
    "defaults": {
      "repo": "stable"
    },
    "log": {
      "enabled": true,
      "file": "/tmp/pakit/main.log",
      "level": "debug"
    },
    "paths": {
      "link": "/tmp/pakit/links",
      "prefix": "/tmp/pakit/builds",
      "recipes": "PLACE1",
      "source": "/tmp/pakit/src"
    },
    "recipe": {
      "update_interval": 86400,
      "uris": [
        {
          "uri": "https://github.com/pakit/base_recipes"
        },
        {
          "uri": "user_recipes"
        }
      ]
    }
  }
}"""

        expect = expect.replace('PLACE0', self.config.filename)
        expect = expect.replace('PLACE1', os.path.expanduser('~/.pakit'))
        print(expect)
        assert str(self.config) == expect

    def test__contains__(self):
        assert 'pakit' in self.config
        assert 'pakit.paths' in self.config
        assert 'pakit.paths.prefix' in self.config
        assert 'beaver' not in self.config
        assert 'canada.beaver' not in self.config

    def test_get(self):
        assert self.config.get('pakit.paths.prefix') == '/tmp/pakit/builds'

    def test_get_missing_key(self):
        self.config.write()
        sub.call(['sed', '-i', '-e', '/command\\|timeout/d',
                  self.config.filename])
        with open(self.config.filename) as fin:
            lines = fin.readlines()
            assert 'command:' not in lines
            assert 'timeout:' not in lines
        config = Config(self.config_file)
        assert config.get('pakit.command.timeout') == 120

    def test_path_to(self):
        expect = pakit.conf.TEMPLATE['pakit']['paths']['link']
        assert self.config.path_to('link') == expect

    def test_path_to_raises(self):
        with pytest.raises(KeyError):
            self.config.path_to('bad_key')

    def test_get_raises(self):
        with pytest.raises(KeyError):
            self.config.get('pakit.paths.prefixxx')

    def test_opts_for(self):
        """ Requires the testing pakit.yml. """
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yml')
        config = Config(config_file)
        opts = config.opts_for('ag')
        assert opts.get('repo') == 'unstable'
        assert opts.get('prefix') == '/tmp/test_pakit/builds'

    def test_set(self):
        self.config.set('pakit.paths.prefix', '/dev/null')
        assert self.config.get('pakit.paths.prefix') == '/dev/null'

        self.config.set('hello.world', True)
        assert self.config.get('hello.world') is True

    def test_write(self):
        self.config.set('pakit.paths.install', 22)
        self.config.write()
        self.config.read()
        assert self.config.get('pakit.paths.install') == 22

    def test_reset(self):
        self.config.set('pakit.paths.prefix', 22)
        self.config.reset()
        assert self.config.get('pakit.paths.prefix') == '/tmp/pakit/builds'


class TestInstallDB(object):
    def setup(self):
        self.config = tc.CONF
        self.idb_file = os.path.join(tc.STAGING, 'test_idb.yml')
        self.idb = InstallDB(self.idb_file)
        self.recipe = pakit.recipe.RDB.get('ag')

    def teardown(self):
        tc.delete_it(self.idb_file)

    def test__str__(self):
        expect = [
            'Config File: ' + self.idb_file,
            'Contents:',
            '{',
            '  "ag": {',
            '    "hash": "d7193e13a7f8f9fe9732e1f546a39e45d3925eb3",',
            '    "repo": "stable",',
            '  }',
            '}'
        ]
        self.recipe.repo = 'stable'
        self.idb.add(self.recipe)
        print(str(self.idb))
        lines = str(self.idb).split('\n')
        del lines[7]
        del lines[4]
        assert expect == lines

    def test__contains__(self):
        self.idb.set('ag', {'hello': 'world'})
        assert 'ag' in self.idb
        assert 'moose' not in self.idb

    def test__iter__(self):
        self.idb.set('ack', 'ack')
        self.idb.set('ag', 'ag')
        actual = sorted([key + obj for key, obj in self.idb])
        assert actual == ['ackack', 'agag']

    def test__delitem__(self):
        self.idb.add(self.recipe)
        assert self.idb['ag']['hash'] == self.recipe.repo.src_hash
        del self.idb['ag']
        with pytest.raises(KeyError):
            self.idb['ag']

    def test__getitem__(self):
        self.idb.add(self.recipe)
        assert self.idb['ag']['hash'] == self.recipe.repo.src_hash
        self.idb.remove('ag')
        with pytest.raises(KeyError):
            self.idb['ag']

    def test_add(self):
        self.idb.add(self.recipe)
        ag = self.idb.get('ag')
        assert ag['hash'] == self.recipe.repo.src_hash

    def test_set(self):
        self.idb.set('ag', {'hello': 'world'})
        entry = self.idb.get('ag')
        assert entry['hello'] == 'world'

    def test_get(self):
        self.idb.add(self.recipe)
        assert self.idb.get('ag') is not None
        assert self.idb.get('ag')['hash'] == self.recipe.repo.src_hash
        self.idb.remove('ag')
        assert self.idb.get('ag') is None

    def test_remove(self):
        self.idb.add(self.recipe)
        self.idb.remove('ag')
        assert self.idb.get('ag') is None

    def test_write(self):
        self.idb.add(self.recipe)
        self.idb.write()
        assert os.path.exists(self.idb_file)

    def test_read(self):
        self.idb.add(self.recipe)
        self.idb.write()
        self.idb.read()
        self.idb = InstallDB(self.idb_file)
        entry = self.idb.get('ag')
        assert entry is not None
        assert entry['hash'] == self.recipe.repo.src_hash

    def test_read_existing(self):
        self.idb.add(self.recipe)
        self.idb.write()
        new_idb = InstallDB(self.idb.filename)
        entry = new_idb.get('ag')
        assert entry is not None
        assert entry['hash'] == self.recipe.repo.src_hash


class TestRecipeURIDB(object):
    def setup(self):
        self.filename = os.path.join(tc.STAGING, 'rdb.yml')
        self.rdb = RecipeURIDB(self.filename)

    def teardown(self):
        tc.delete_it(self.filename)

    def test_add_local(self):
        self.rdb.add('local', 'local', False)
        assert self.rdb['local']['path'] == 'local'
        assert self.rdb['local']['is_vcs'] is False

    def test_add_remote(self):
        self.rdb.add('remote_uri', 'remote_path', True)
        assert self.rdb['remote_uri']['path'] == 'remote_path'
        assert self.rdb['remote_uri']['is_vcs']

    def test_add_remote_kwargs(self):
        kwargs = {'tag': '0.30.0'}
        self.rdb.add('remote_uri', 'remote_path', True, kwargs)
        assert self.rdb['remote_uri']['path'] == 'remote_path'
        assert self.rdb['remote_uri']['is_vcs']
        assert self.rdb['remote_uri']['kwargs'] == kwargs

    def test_update_time(self):
        self.rdb.add('local', 'local', False)
        old_time = self.rdb['local']['time']
        self.rdb.update_time('local')
        assert self.rdb['local']['time'] > old_time

    def test_need_updates(self):
        key = 'remote_uri'
        self.rdb.add(key, 'remote_path', True)
        self.rdb[key]['time'] = self.rdb[key]['time'] - 10000
        assert self.rdb.need_updates(5000) == ['remote_uri']

    def test_select_path_preferred(self):
        preferred = '/tmp/first'
        assert self.rdb.select_path(preferred) == preferred

    def test_select_path_collision(self):
        preferred = '/tmp/first'
        self.rdb.add('first', preferred, False)
        assert self.rdb.select_path(preferred) == preferred + '_1'
