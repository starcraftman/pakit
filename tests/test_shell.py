""" Test command execution class. """
from __future__ import absolute_import, print_function

import os
import shutil

from wok.main import global_init
from wok.shell import Git, Hg, Command

class TestGit(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.test_dir = './temp'
        git_url = 'https://github.com/ggreer/the_silver_searcher'
        self.repo = Git(git_url, target=self.test_dir, tag='0.29.0')

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_hash(self):
        assert self.repo.cur_hash == '808b32de91196b4a9a571e75ac96efa58ca90b99'

    def test_branch(self):
        assert self.repo.tag == '0.29.0'
        assert self.repo._VersionRepo__on_branch is False

        self.repo.tag = 'hello'
        assert self.repo.tag == 'hello'
        assert self.repo._VersionRepo__on_branch is False

    def test_tag(self):
        self.repo.branch = 'hello'
        assert self.repo.branch == 'hello'
        assert self.repo._VersionRepo__on_branch is True

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

    def test_checkout(self):
        self.repo.download()
        self.repo.tag = '0.20.0'
        self.repo.checkout()
        assert self.repo.cur_hash == '20d62b4e3f88c4e38fead73cc4030d8bb44c7259'

    def test__str__(self):
        uri = 'https://github.com/user/repo'
        tag = 'default'
        repo_tag = Git(uri, tag=tag)
        repo_branch = Git(uri, branch=tag)

        print()
        print(str(repo_tag))
        print(str(repo_branch))

        assert str(repo_branch) == 'Git: branch: {0}, uri: {1}'.format(tag, uri)
        assert str(repo_tag) == 'Git: tag: {0}, uri: {1}'.format(tag, uri)

class TestHg(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.test_dir = './temp'
        hg_url = 'https://bitbucket.org/sjl/hg-prompt/'
        self.repo = Hg(hg_url, target=self.test_dir, tag='0.2')

    def teardown(self):
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test_hash(self):
        assert self.repo.cur_hash == '80:a6ec48f03985'

    def test_download(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.hg'))

    def test_is_cloned(self):
        assert not self.repo.is_cloned
        self.repo.download()
        assert self.repo.is_cloned

    def test_checkout(self):
        self.repo.download()
        self.repo.tag = '0.1'
        self.repo.checkout()
        assert self.repo.cur_hash == '14:d390b5e27191'

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
