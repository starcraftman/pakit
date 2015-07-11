""" Test command execution class. """
from __future__ import absolute_import

import os
import pytest
import shutil
import time

from wok.shell import *

class TestGit(object):
    def setup(self):
        self.test_dir = './temp'
        self.url = 'https://github.com/ggreer/the_silver_searcher'
        self.git = Git(self.url, self.test_dir)

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_download(self):
        self.git.download()
        assert os.path.exists(os.path.join(self.git.target, '.git'))

    def test_is_cloned(self):
        assert not self.git.is_cloned
        self.git.download()
        assert self.git.is_cloned

    def test_target(self):
        os.mkdir(self.test_dir)
        with pytest.raises(IOError):
            self.git.target = self.test_dir

    #def test_tag_set(self):
        #self.git.download()

    def test_clean(self):
        self.git.download()
        self.git.clean()
        assert not os.path.exists(self.git.target)

    def test_version(self):
        self.git.tag = '0.29.0'
        self.git.download()
        assert self.git.version == 'commit 808b32de91196b4a9a571e75ac96efa58ca90b99'

class TestVCS(object):
    def setup(self):
        self.test_dir = './temp'

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
        cmd.wait()
        assert cmd.rcode == 0

    def test_hg(self):
        hg_url = 'https://bitbucket.org/sjl/hg-prompt/'
        get_hg(url=hg_url, target=self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, '.hg'))

        cmd = Command('hg status', self.test_dir)
        cmd.wait()
        assert cmd.rcode == 0

    @pytest.mark.skipif('os.path.expanduser("~") != "/home/travis"', reason='Long Test')
    def test_svn(self):
        svn_url = 'http://svn.apache.org/repos/asf/spamassassin/trunk'
        get_svn(url=svn_url, target=self.test_dir)
        assert os.path.exists(os.path.join(self.test_dir, '.svn'))

        cmd = Command('svn status', self.test_dir)
        cmd.wait()
        assert cmd.rcode == 0

class TestCommand(object):
    def test_simple_command(self):
        cmd = Command('echo "Hello"')
        cmd.wait()
        assert cmd.rcode == 0

    def test_command_dir(self):
        try:
            os.makedirs('dummy')
            with open('dummy/hello', 'w+b') as out:
                out.write('this is a sample line')

            cmd = Command('ls', os.path.abspath('./dummy'))
            cmd.wait()

            assert cmd.rcode == 0
            assert cmd.output() == ['hello']
        finally:
            shutil.rmtree('dummy')

    def test_output(self):
        cmd = Command('echo "Hello py.test"')
        cmd.wait()
        lines = cmd.output()
        assert lines == ['Hello py.test']

    def test_terminate(self):
        cmd = Command('sleep 4')
        assert cmd.alive
        cmd.terminate()
        assert not cmd.alive
