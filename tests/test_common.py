"""
Test tests.common
"""
from __future__ import absolute_import, print_function

import mock
import os

import tests.common as tc


def test_env_setup():
    tc.env_setup()
    expect = ['arcs', 'git', 'hg', 'tmux.tar.gz']
    for exp in expect:
        assert exp in os.listdir(tc.STAGING)


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
