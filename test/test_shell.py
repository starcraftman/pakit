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
        git_url = 'https://github.com/ggreer/the_silver_searcher'
        self.repo = Git(git_url, self.test_dir)

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_commit(self):
        self.repo.tag = '0.29.0'
        self.repo.download()
        assert self.repo.commit == 'commit 808b32de91196b4a9a571e75ac96efa58ca90b99'

    def test_clean(self):
        self.repo.download()
        self.repo.clean()
        assert not os.path.exists(self.repo.target)

    def test_download(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.git'))

    def test_is_cloned(self):
        assert not self.repo.is_cloned
        self.repo.download()
        assert self.repo.is_cloned

    def test_target(self):
        os.mkdir(self.test_dir)
        with pytest.raises(IOError):
            self.repo.target = self.test_dir

    def test_with_func(self):
        repo_git = os.path.join(self.repo.target, '.git')
        with self.repo:
            assert os.path.exists(repo_git)
        assert not os.path.exists(repo_git)

class TestHg(object):
    def setup(self):
        self.test_dir = './temp'
        hg_url = 'https://bitbucket.org/sjl/hg-prompt/'
        self.repo = Hg(hg_url, self.test_dir)

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_commit(self):
        self.repo.tag = '0.2'
        self.repo.download()
        assert self.repo.commit == 'changeset:   80:a6ec48f03985'

    def test_download(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.hg'))

    def test_is_cloned(self):
        assert not self.repo.is_cloned
        self.repo.download()
        assert self.repo.is_cloned

class TestVCS(object):
    def setup(self):
        self.test_dir = './temp'

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

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
