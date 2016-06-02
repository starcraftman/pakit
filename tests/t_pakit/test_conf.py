"""
Test pakit.conf
"""
from __future__ import absolute_import, print_function
import os
import subprocess as sub
import mock
import pytest

import pakit.conf
from pakit.conf import Config, InstallDB, RecipeURIDB, YamlDict, YamlNestedDict
import pakit.recipe
import tests.common as tc


class TestYamlDict(object):
    def setup(self):
        self.fname = os.path.join(tc.STAGING, 'file.yaml')
        self.dict = YamlDict(self.fname, {'a': 11, 'b': 'hello'})

    def teardown(self):
        tc.delete_it(self.fname)

    def test__getitem__(self):
        assert self.dict['a'] == 11
        with pytest.raises(KeyError):
            assert self.dict['doesnotexist']
        assert self.dict.get('does.not.exist', 42) == 42

    def test__setitem__(self):
        self.dict['c'] = 'void'
        assert self.dict['c'] == 'void'

    def test__delitem__(self):
        del self.dict['b']
        with pytest.raises(KeyError):
            assert self.dict['b']

    def test__contains__(self):
        assert 'b' in self.dict
        assert 'doesnotexist' not in self.dict

    def test__len__(self):
        assert len(self.dict) == 2

    def test__iter__(self):
        assert [x for x in self.dict] == ['a', 'b']

    def test__str__(self):
        expect = """Class: YamlDict
Filename: %s
{
  "a": 11,
  "b": "hello"
}""" % self.fname
        assert str(self.dict) == expect

    def test_filename(self):
        assert self.dict.filename == self.fname
        self.dict.filename = 'aaa'
        assert self.dict.filename == 'aaa'

    def test_read(self):
        with open(self.dict.filename, 'wb') as fout:
            fout.write('hello: world\n'.encode())
        self.dict.read()
        assert self.dict['hello'] == 'world'

    @mock.patch('pakit.conf.logging')
    def test_read_from_file_invalid(self, mock_log):
        assert not os.path.exists(self.dict.filename)
        self.dict.read()
        assert mock_log.error.called

    def test_write(self):
        self.dict.clear()
        self.dict['hello'] = 'world'
        self.dict.write()
        assert os.path.exists(self.dict.filename)
        with open(self.dict.filename) as fin:
            assert fin.readlines() == ['hello: world\n']


class TestYamlNestedDict(object):
    def setup(self):
        self.fname = os.path.join(tc.STAGING, 'file.yaml')
        self.dict = YamlNestedDict(self.fname, {'a': 11, 'b': 'hello',
                                   'c': {'inner': 'world'}})

    def teardown(self):
        tc.delete_it(self.fname)

    def test__getitem__(self):
        assert self.dict['a'] == 11
        assert self.dict['c.inner'] == 'world'
        with pytest.raises(KeyError):
            assert self.dict['does.not.exist']
        assert self.dict.get('does.not.exist', 42) == 42

    def test__setitem__(self):
        self.dict['c.inner'] = 'void'
        assert self.dict['c.inner'] == 'void'
        self.dict['d.e.f'] = 'next 3'
        assert self.dict['d.e.f'] == 'next 3'

    def test__delitem__(self):
        del self.dict['c.inner']
        with pytest.raises(KeyError):
            assert self.dict['c.inner']

    def test__contains__(self):
        assert 'c.inner' in self.dict
        assert 'does.not.exist' not in self.dict


class TestConfig(object):
    """ Test the operation of Config class. """
    def setup(self):
        self.config_file = os.path.join(tc.STAGING, 'pakit.yml')
        self.config = Config(self.config_file)

    def teardown(self):
        tc.delete_it(self.config_file)

    def test_get_default(self):
        assert self.config.get('pakit.paths.prefixxx', 42) == 42

    def test_get_raises(self):
        with pytest.raises(KeyError):
            assert self.config['pakit.paths.prefixxx']

    def test_get_missing_key(self):
        self.config.write()
        sub.call(['sed', '-i', '-e', '/command\\|timeout/d',
                  self.config.filename])
        with open(self.config.filename) as fin:
            lines = fin.readlines()
            print(lines)
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

    def test_opts_for(self):
        """ Requires the testing pakit.yml. """
        config = Config(tc.TEST_CONFIG)
        opts = config.opts_for('ag')
        assert opts.get('repo') == 'unstable'
        assert opts.get('prefix') == '/tmp/test_pakit/builds'

    def test_reset(self):
        self.config['pakit.paths.prefix'] = 22
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

    def test_add(self):
        self.idb.add(self.recipe)
        ag_recipe = self.idb.get('ag')
        assert ag_recipe['hash'] == self.recipe.repo.src_hash

    def test_get(self):
        self.idb.add(self.recipe)
        assert self.idb.get('ag') is not None
        assert self.idb.get('ag')['hash'] == self.recipe.repo.src_hash
        self.idb.remove('ag')
        assert self.idb.get('ag') is None


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
