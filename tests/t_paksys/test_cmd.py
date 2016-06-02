"""
Test paksys.cmd
"""
from __future__ import absolute_import, print_function
import os
import mock
import pytest

import pakit.conf
from pakit.exc import PakitCmdError, PakitCmdTimeout
from paksys.cmd import Command, cmd_kwargs, cmd_cleanup
import tests.common as tc


@mock.patch('paksys.cmd.shutil')
def test_cmd_cleanup(mock_shutil):
    cmd_cleanup()
    mock_shutil.rmtree.assert_called_with(pakit.conf.TMP_DIR)


def test_cmd_kwargs_empty():
    import subprocess
    kwargs = {}
    cmd_kwargs(kwargs)
    assert len(kwargs) == 6
    assert kwargs['stdin'] is None
    assert '/tmp' in kwargs['stdout'].name
    assert kwargs['stderr'] == subprocess.STDOUT
    assert kwargs['preexec_fn'] is os.setsid
    assert kwargs['env'] is None
    assert kwargs['wait']


def test_cmd_kwargs_prevcmd():
    cmd = Command('ls')
    kwargs = {'prev_cmd': cmd}
    cmd_kwargs(kwargs)
    assert kwargs['stdin']


def test_cmd_kwargs_newenv():
    kwargs = {'env': {'HELLO': 'WORLD'}}
    cmd_kwargs(kwargs)
    assert 'PATH' in kwargs['env']
    assert 'HELLO' in kwargs['env']


class TestCommand(object):
    def test_simple_command(self):
        cmd = Command('echo "Hello"')
        assert cmd.rcode == 0

    def test_simple_command_list(self):
        cmd = Command(['echo', '"Hello"'])
        assert cmd.rcode == 0

    def test_command_dir(self):
        try:
            os.makedirs('dummy')
            with open('dummy/hello', 'wb') as fout:
                fout.write('this is a sample line'.encode())

            cmd = Command('ls', os.path.abspath('./dummy'))

            assert cmd.rcode == 0
            assert cmd.output() == ['hello']
        finally:
            tc.delete_it('dummy')

    def test_output(self):
        cmd = Command('echo "Hello py.test"')
        lines = cmd.output()
        assert lines == ['Hello py.test']

    def test_terminate(self):
        cmd = Command('sleep 4', wait=False)
        assert cmd.alive
        cmd.terminate()
        assert not cmd.alive

    def test_cmd_not_available(self):
        with pytest.raises(PakitCmdError):
            Command('not_a_command_anywhere')

    def test_relative_cmd_not_available(self):
        with pytest.raises(PakitCmdError):
            Command('./not_a_command_anywhere')

    def test_cwd_does_not_exist(self):
        with pytest.raises(PakitCmdError):
            Command('pwd', cwd='/tmp/should_not_exist/at_all')

    def test_cmd_rcode_not_zero(self):
        with pytest.raises(PakitCmdError):
            Command('grep --aaaaa')

    def test_cmd_timeout(self):
        with pytest.raises(PakitCmdTimeout):
            Command('sleep 20', wait=False).wait(2)

    def test_prev_cmd_stdin(self):
        cmd = Command('echo -e "Hello\nGoodbye!"')
        cmd2 = Command('grep "ood"', prev_cmd=cmd)
        assert cmd2.output() == ['Goodbye!']

    def test_env_override(self):
        old_environ = os.environ.copy()
        os.environ['HELLO'] = 'bad'
        cmd = Command(['env'], env={'HELLO': 'pakit'})
        'HELLO=pakit' in cmd.output()
        os.environ = old_environ
