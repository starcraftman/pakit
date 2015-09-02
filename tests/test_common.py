"""
Test tests.common
"""
import mock
import os

import tests.common as tc


def test_env_setup():
    tc.env_setup()
    expect = ['archive', 'git', 'hg', 'tmux.tar.gz']
    assert sorted(os.listdir(tc.STAGING)) == expect


@mock.patch('tests.common.shutil')
@mock.patch('tests.common.delete_it')
def test_env_teardown(mock_delete_it, mock_shutil):
    tc.env_setup()
    tc.env_teardown()
    assert mock_delete_it.called is True
    for path in tc.PATHS:
        assert mock_delete_it.called_with(path)
    assert mock_shutil.move.called is True


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
