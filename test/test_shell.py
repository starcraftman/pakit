""" Test command execution class. """
from __future__ import absolute_import

import os
import pytest
import shutil
import time

from wok.shell import *

class TestVCS(object):
    def setup(self):
        self.test_dir = os.path.abspath('./temp')

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_git(self):
        git_url = 'https://github.com/ggreer/the_silver_searcher'
        get_git(url=git_url, target=self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, '.git'))

        cmd = Command('git status', self.test_dir)
        cmd.execute()
        cmd.wait()
        assert cmd.rcode == 0

    def test_hg(self):
        hg_url = 'https://bitbucket.org/sjl/hg-prompt/'
        get_hg(url=hg_url, target=self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, '.hg'))

        cmd = Command('hg status', self.test_dir)
        cmd.execute()
        cmd.wait()
        assert cmd.rcode == 0

    @pytest.mark.skipif('os.path.expanduser("~") != "/home/travis"', reason='Long Test')
    def test_svn(self):
        svn_url = 'http://svn.apache.org/repos/asf/spamassassin/trunk'
        get_svn(url=svn_url, target=self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, '.svn'))

        cmd = Command('svn status', self.test_dir)
        cmd.execute()
        cmd.wait()
        assert cmd.rcode == 0

class TestCommand(object):
    def test_simple_command(self):
        cmd = Command('echo "Hello"')
        cmd.execute()
        cmd.wait()
        assert cmd.rcode == 0

    def test_command_dir(self):
        try:
            os.makedirs('dummy')
            with open('dummy/hello', 'w+b') as out:
                out.write('this is a sample line')

            cmd = Command('ls', os.path.abspath('./dummy'))
            cmd.execute()
            cmd.wait()

            assert cmd.rcode == 0
            assert cmd.output() == ['hello']
        finally:
            shutil.rmtree('dummy')

    def test_output(self):
        cmd = Command('echo "Hello py.test"')
        cmd.execute()
        cmd.wait()
        lines = cmd.output()
        assert lines == ['Hello py.test']

    def test_terminate(self):
        cmd = Command('sleep 4')
        cmd.execute()
        assert cmd.alive
        cmd.terminate()
        assert not cmd.alive
