"""
test paksys.vcs
"""
from __future__ import absolute_import, print_function
import os
import pytest

from pakit.exc import PakitError
from paksys.cmd import Command
from paksys.vcs import Git, Hg, vcs_factory
import tests.common as tc


def test_vcs_factory():
    print(os.listdir('/tmp'))
    repo = vcs_factory(tc.GIT)
    assert isinstance(repo, Git)
    assert repo.uri == tc.GIT


def test_vcs_factory_unsupported():
    with pytest.raises(PakitError):
        vcs_factory(tc.TAR)


class TestGit(object):
    def setup(self):
        self.test_dir = os.path.join(tc.CONF.path_to('source'), 'git')
        git_url = os.path.join(tc.STAGING, 'git')
        self.repo = Git(git_url, target=self.test_dir, tag='0.29.0')

    def teardown(self):
        tc.delete_it(self.test_dir)

    def test_hash(self):
        assert self.repo.src_hash == '808b32de91196b4a9a571e75ac96efa58ca90b99'

    def test_tag(self):
        assert self.repo.tag == '0.29.0'
        assert self.repo.on_branch is False

        self.repo.tag = 'hello'
        assert self.repo.tag == 'hello'
        assert self.repo.on_branch is False

    def test_branch(self):
        self.repo.branch = 'hello'
        assert self.repo.branch == 'hello'
        assert self.repo.on_branch

    def test_clean(self):
        self.repo.download()
        self.repo.clean()
        assert not os.path.exists(self.repo.target)

    def test_download_with_tag(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.git'))

    def test_download_with_branch(self):
        repo = Git(self.repo.uri, target=self.test_dir)
        with repo:
            assert os.path.exists(os.path.join(repo.target, '.git'))
            assert repo.on_branch
            assert repo.branch == 'master'

    def test_ready(self):
        assert not self.repo.ready
        self.repo.download()
        assert self.repo.ready

    def test_checkout(self):
        self.repo.download()
        self.repo.tag = '0.20.0'
        tag_hash = '20d62b4e3f88c4e38fead73cc4030d8bb44c7259'
        with self.repo:
            assert self.repo.src_hash == tag_hash

    def test_reset(self):
        temp_file = os.path.join(self.repo.target, 'tempf')
        with self.repo:
            assert not os.path.exists(temp_file)
            with open(temp_file, 'wb') as fout:
                fout.write('hello'.encode())
        assert not os.path.exists(temp_file)

    def test_update(self):
        def get_hash(target):
            """
            Required because with now forces right commit
            """
            cmd = Command('git log -1 ', target)
            return cmd.output()[0].split()[-1]

        self.repo.branch = 'master'
        with self.repo:
            # Lop off history to ensure updateable
            latest_hash = self.repo.src_hash
            Command('git reset --hard HEAD~3', self.repo.target)
            assert get_hash(self.repo.target) != latest_hash
            self.repo.update()
            assert get_hash(self.repo.target) == latest_hash

    def test__str__(self):
        uri = 'https://github.com/user/repo'
        tag = 'master'
        repo_tag = Git(uri, tag=tag)
        repo_branch = Git(uri, branch=tag)

        print()
        print(str(repo_tag))
        print(str(repo_branch))

        expect = 'Git: branch: {0}, uri: {1}'.format(tag, uri)
        assert str(repo_branch) == expect
        assert str(repo_tag) == 'Git: tag: {0}, uri: {1}'.format(tag, uri)

    def test_valid_uri(self):
        assert Git.valid_uri(self.repo.uri)
        assert not Git.valid_uri('www.google.com')


class TestHg(object):
    def setup(self):
        self.test_dir = os.path.join(tc.CONF.path_to('source'), 'hg')
        hg_url = os.path.join(tc.STAGING, 'hg')
        self.repo = Hg(hg_url, target=self.test_dir, tag='0.2')

    def teardown(self):
        tc.delete_it(self.test_dir)

    def test_hash(self):
        assert self.repo.src_hash == 'a6ec48f03985'

    def test_download_with_tag(self):
        with self.repo:
            assert os.path.exists(os.path.join(self.repo.target, '.hg'))

    def test_download_with_branch(self):
        repo = Hg(self.repo.uri, target=self.test_dir)
        with repo:
            assert os.path.exists(os.path.join(repo.target, '.hg'))
            assert repo.on_branch
            assert repo.branch == 'default'

    def test_ready(self):
        assert not self.repo.ready
        with self.repo:
            assert self.repo.ready

    def test_checkout(self):
        repo = Hg('https://bitbucket.org/olauzanne/pyquery',
                  target=self.test_dir)
        repo.download()
        repo.tag = 'manipulating'
        with repo:
            assert repo.src_hash == '3c7ab75c2eea'

    def test_reset(self):
        temp_file = os.path.join(self.repo.target, 'tempf')
        with self.repo:
            assert not os.path.exists(temp_file)
            with open(temp_file, 'wb') as fout:
                fout.write('hello'.encode())
        assert not os.path.exists(temp_file)

    def test_update(self):
        def get_hash(target):
            """
            Required because with now forces right commit
            """
            cmd = Command('hg identify', target)
            return cmd.output()[0].split()[0]

        self.repo.branch = 'default'
        with self.repo:
            # Lop off history to ensure updateable
            latest_hash = self.repo.src_hash
            Command('hg strip tip', self.repo.target)
            assert get_hash(self.repo.target) != latest_hash
            self.repo.update()
            assert get_hash(self.repo.target) == latest_hash

    def test_valid_uri(self):
        assert Hg.valid_uri(self.repo.uri)
        assert not Hg.valid_uri('www.google.com')
