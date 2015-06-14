""" Test command execution class. """
from __future__ import absolute_import

import os
import pytest
import shutil
import time

from wok.shell import Command

class TestCommand:
    def test_simple_command(self):
        cmd = Command('echo "Hello"')
        cmd.execute()
        cmd.wait()
        assert cmd.rcode == 0

    def test_command_dir(self):
        os.makedirs('dummy')
        with open('dummy/hello', 'w+b') as out:
            out.write('this is a sample line')

        cmd = Command('ls', 'dummy')
        cmd.execute()
        cmd.wait()

        assert cmd.rcode == 0
        assert cmd.output() == ['hello']

        shutil.rmtree('dummy')

    def test_output(self):
        cmd = Command('echo "Hello py.test"')
        cmd.execute()
        cmd.wait()
        lines = cmd.output()
        assert type(lines) == type([])
        assert lines == ['Hello py.test']

    def test_terminate(self):
        cmd = Command('cat -')
        cmd.execute()
        assert cmd.alive
        cmd.terminate()
        assert not cmd.alive

