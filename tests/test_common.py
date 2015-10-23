"""
Test tests.common
"""
from __future__ import absolute_import, print_function

import mock
import os
import shutil

import tests.common as tc


def assert_files_same(file1, file2):
    """
    Return true iff file1 has same contents as file2.
    """
    with open(file1, 'r') as fin:
        lines1 = fin.readlines()

    with open(file2, 'r') as fin:
        lines2 = fin.readlines()

    assert len(lines1) == len(lines2)
    for num, line in enumerate(lines1):
        assert line == lines2[num]


class TestEnvConfig(object):
    def setup(self):
        self.config = os.path.abspath('./.pakit.yml')
        self.config_bak = self.config + '_bak'
        self.message = 'hello world'

    def teardown(self):
        tc.delete_it(self.config)
        tc.delete_it(self.config_bak)

    def test_env_config_without_backup(self):
        try:
            bak_conf = self.config + 'bak'
            if os.path.exists(self.config):
                shutil.move(self.config, bak_conf)

            assert not os.path.exists(self.config)
            assert not os.path.exists(self.config_bak)

            tc.env_config_setup()
            assert os.path.exists(self.config)
            assert not os.path.exists(self.config_bak)
            assert_files_same(self.config, tc.TEST_CONFIG)

            tc.env_config_teardown()
            assert not os.path.exists(self.config)
            assert not os.path.exists(self.config_bak)
        finally:
            if os.path.exists(bak_conf):
                shutil.move(bak_conf, self.config)

    def test_env_config_with_backup(self):
        template = self.config + '_temp'
        with open(self.config, 'w') as fout:
            fout.write(self.message)
        with open(template, 'w') as fout:
            fout.write(self.message)

        assert os.path.exists(self.config)
        assert not os.path.exists(self.config_bak)

        tc.env_config_setup()
        assert os.path.exists(self.config)
        assert os.path.exists(self.config_bak)
        assert_files_same(self.config, tc.TEST_CONFIG)
        assert_files_same(self.config_bak, template)

        tc.env_config_teardown()
        assert os.path.exists(self.config)
        assert not os.path.exists(self.config_bak)
        assert_files_same(self.config, template)

        os.remove(template)


def test_env_setup():
    tc.env_setup()
    expect = ['arcs', 'git', 'hg', 'tmux.tar.gz']
    assert sorted(os.listdir(tc.STAGING)) == expect


@mock.patch('tests.common.shutil')
@mock.patch('tests.common.delete_it')
def test_env_teardown(mock_delete_it, mock_shutil):
    tc.env_setup()
    tc.env_teardown()
    assert mock_delete_it.called
    for path in tc.PATHS:
        assert mock_delete_it.called_with(path)
    assert mock_shutil.move.called


def test_env_status(mock_print):
    tc.env_status()
    mock_print.assert_any_call('IDB Entries: ', [])
    mock_print.assert_any_call('Contents Link Dir: ', [])
    mock_print.assert_any_call('Contents Prefix Dir: ', [])


def test_delete_it_file():
    afile = 'dummy'
    with open(afile, 'wb') as fout:
        fout.write('A simple line.'.encode())
    tc.delete_it(afile)
    assert not os.path.exists(afile)


def test_delete_it_dir():
    os.makedirs('tdir')
    afile = os.path.join('tdir', 'dummy')
    for i in range(0, 5):
        with open(afile + str(i), 'wb') as fout:
            fout.write('A simple line.'.encode())
    tc.delete_it('tdir')
    assert not os.path.exists('tdir')


def test_mock_print(mock_print):
    assert isinstance(mock_print, mock.MagicMock)
    print('hello')
    mock_print.assert_called_with('hello')
