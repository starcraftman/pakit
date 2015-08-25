""" Test command execution class. """
from __future__ import absolute_import, print_function

import os
import pytest
import shutil

from pakit.exc import PakitError
from pakit.main import global_init
from pakit.shell import (Git, Hg, Command, Archive, CmdFailed, find_arc_name,
                         cmd_cleanup, get_extract_func, extract_tar_gz)
import pakit.shell


TAR_URL = 'http://sourceforge.net/projects/tmux/files/tmux/tmux-2.0/' \
          'tmux-2.0.tar.gz/download?use_mirror=hivelocity'

def test_find_arc_name():
    assert find_arc_name(TAR_URL)[0] == 'tmux-2.0.tar.gz'

def test_find_arc_name_fail():
    with pytest.raises(PakitError):
        find_arc_name('archive.not.an.arc')

def test_get_extract_func():
    assert get_extract_func('tar.gz') is extract_tar_gz

def test_get_extract_func_not_found():
    with pytest.raises(PakitError):
        get_extract_func('tar.gzzz')

class TestExtractFuncs(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
        self.config = global_init(config_file)
        self.arc_dir = 'arcs'
        self.target = 'temp'
        self.expect_file = os.path.join(self.target, 'example.txt')
        cmd = Command('git clone https://github.com/pakit/arc_fmts.git ' + self.arc_dir)
        cmd.wait()

    def teardown(self):
        try:
            shutil.rmtree(self.arc_dir)
        except OSError:
            pass
        try:
            shutil.rmtree(self.target)
        except OSError:
            pass

    def arc_file(self, ext):
        return os.path.join(self.arc_dir, 'example.' + ext)

    def __test_ext(self, ext):
        extract = get_extract_func(ext)
        extract(self.arc_file(ext), self.target)
        assert os.listdir(os.path.dirname(self.expect_file)) == ['example.txt']

    def test_tb2(self):
        self.__test_ext('tb2')

    def test_tbz(self):
        self.__test_ext('tbz')

    def test_tbz2(self):
        self.__test_ext('tbz2')

    def test_tgz(self):
        self.__test_ext('tgz')

    def test_tar_bz2(self):
        self.__test_ext('tar.bz2')

    def test_tar_gz(self):
        self.__test_ext('tar.gz')

    def test_zip(self):
        self.__test_ext('zip')

class TestArchive(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
        self.config = global_init(config_file)
        self.test_arc = 'tmux-2.0.tar.gz'
        self.test_dir = './temp'
        self.archive = Archive(TAR_URL, target=self.test_dir,
                               hash='977871e7433fe054928d86477382bd5f6794dc3d')

    def teardown(self):
        try:
            os.remove(self.test_arc)
        except OSError:
            pass
        try:
            shutil.rmtree(self.test_dir)
        except OSError:
            pass

    def test__str__(self):
        expect = 'Archive: ' + self.archive.uri
        assert str(self.archive) == expect

    def test_download(self):
        self.archive.download()
        assert os.path.exists(self.test_arc)

    def test_download_bad_hash(self):
        archive = Archive(TAR_URL, target=self.test_dir,
                               hash='bad hash')
        with pytest.raises(PakitError):
            archive.download()

    def test_extract(self):
        self.archive.get_it()
        assert os.path.exists(self.test_dir)
        assert len(os.listdir(self.test_dir)) != 0

    def test_hash(self):
        self.archive.get_it()
        assert self.archive.cur_hash == self.archive.file_hash
        assert self.archive.file_hash == '977871e7433fe054928d86477382bd5f6794dc3d'

    def test_clean(self):
        self.archive.download()
        self.archive.clean()
        assert not os.path.exists(self.archive.target)

class TestGit(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
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

    def test_tag(self):
        assert self.repo.tag == '0.29.0'
        assert self.repo.on_branch is False

        self.repo.tag = 'hello'
        assert self.repo.tag == 'hello'
        assert self.repo.on_branch is False

    def test_branch(self):
        self.repo.branch = 'hello'
        assert self.repo.branch == 'hello'
        assert self.repo.on_branch is True

    def test_clean(self):
        self.repo.download()
        self.repo.clean()
        assert not os.path.exists(self.repo.target)

    def test_download_with_tag(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.git'))

    def test_download_with_branch(self):
        repo = Git(self.repo.uri, target=self.test_dir)
        assert repo.branch is None
        repo.download()
        assert os.path.exists(os.path.join(repo.target, '.git'))
        assert repo.on_branch is True
        assert repo.branch == 'master'

    def test_ready(self):
        assert not self.repo.ready
        self.repo.download()
        assert self.repo.ready

    def test_checkout(self):
        self.repo.download()
        self.repo.tag = '0.20.0'
        self.repo.checkout()
        assert self.repo.cur_hash == '20d62b4e3f88c4e38fead73cc4030d8bb44c7259'

    def test_update(self):
        self.repo.branch = 'master'
        self.repo.download()

        # Lop off history to ensure updateable
        latest_hash = self.repo.cur_hash
        cmd = Command('git reset --hard HEAD~3', self.repo.target)
        cmd.wait()
        assert self.repo.cur_hash != latest_hash
        self.repo.update()
        assert self.repo.cur_hash == latest_hash

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
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
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

    def test_download_with_tag(self):
        self.repo.download()
        assert os.path.exists(os.path.join(self.repo.target, '.hg'))

    def test_download_with_branch(self):
        repo = Hg(self.repo.uri, target=self.test_dir)
        assert repo.branch is None
        repo.download()
        assert os.path.exists(os.path.join(repo.target, '.hg'))
        assert repo.on_branch is True
        assert repo.branch == 'default'

    def test_ready(self):
        assert not self.repo.ready
        self.repo.download()
        assert self.repo.ready

    def test_checkout(self):
        self.repo.download()
        self.repo.tag = '0.1'
        self.repo.checkout()
        assert self.repo.cur_hash == '14:d390b5e27191'

    def test_update(self):
        self.repo.branch = 'default'
        self.repo.download()

        # Lop off history to ensure updateable
        latest_hash = self.repo.cur_hash
        cmd = Command('hg strip tip', self.repo.target)
        cmd.wait()
        assert self.repo.cur_hash != latest_hash
        self.repo.update()
        assert self.repo.cur_hash == latest_hash

def test_cmd_cleanup():
    cmd_file = os.path.join(pakit.shell.TMP_DIR, 'cmd1')
    with open(cmd_file, 'w+b') as fout:
        fout.write('hello'.encode())

    assert os.path.exists(cmd_file)
    cmd_cleanup()
    assert not os.path.exists(cmd_file)

class TestCommand(object):
    def test_simple_command(self):
        cmd = Command('echo "Hello"')
        cmd.wait()
        assert cmd.rcode == 0

    def test_simple_command_list(self):
        cmd = Command(['echo', '"Hello"'])
        cmd.wait()
        assert cmd.rcode == 0

    def test_command_dir(self):
        try:
            os.makedirs('dummy')
            with open('dummy/hello', 'w+b') as fout:
                fout.write('this is a sample line'.encode())

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

    def test_failed_cmd(self):
        cmd = Command('false')
        with pytest.raises(CmdFailed):
            cmd.wait()
