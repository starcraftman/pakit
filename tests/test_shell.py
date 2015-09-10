"""
Test pakit.shell
"""
from __future__ import absolute_import, print_function

import mock
import os
import pytest
import shutil

from pakit.exc import PakitError, PakitCmdError, PakitCmdTimeout
from pakit.shell import (Git, Hg, Command, Archive, find_arc_name,
                         hash_archive, cmd_cleanup, get_extract_func,
                         extract_tar_gz)
import pakit.shell
import tests.common as tc


def test_find_arc_name():
    assert find_arc_name(tc.TAR)[0] == 'tmux-2.0.tar.gz'


def test_find_arc_name_fail():
    with pytest.raises(PakitError):
        find_arc_name('archive.not.an.arc')


def test_get_extract_func():
    assert get_extract_func('tar.gz') is extract_tar_gz


def test_get_extract_func_not_found():
    with pytest.raises(PakitError):
        get_extract_func('tar.gzzz')


def test_hash_archive_sha1():
    expect_hash = '977871e7433fe054928d86477382bd5f6794dc3d'
    arc = Archive(tc.TAR, target='./temp', hash=expect_hash)
    arc.download()
    assert hash_archive(arc.arc_file, 'sha1') == expect_hash
    os.remove(arc.arc_file)


def test_cmd_cleanup():
    cmd_file = os.path.join(pakit.shell.TMP_DIR, 'cmd1')
    with open(cmd_file, 'wb') as fout:
        fout.write('hello'.encode())

    assert os.path.exists(cmd_file)
    cmd_cleanup()
    assert not os.path.exists(cmd_file)


def test_cmd_cleanup_raises():
    cmd_file = os.path.join(pakit.shell.TMP_DIR, 'cmd1')
    os.makedirs(cmd_file)

    assert os.path.exists(cmd_file)
    with pytest.raises(OSError):
        cmd_cleanup()
    assert os.path.exists(cmd_file)
    os.rmdir(cmd_file)


class TestExtractFuncs(object):
    def setup(self):
        self.config = tc.env_setup()
        self.arc_dir = 'arcs'
        self.target = 'temp'
        self.expect_file = os.path.join(self.target, 'example.txt')
        cmd = Command('git clone https://github.com/pakit/arc_fmts.git '
                      + self.arc_dir)
        cmd.wait()

    def teardown(self):
        tc.delete_it(self.arc_dir)
        tc.delete_it(self.target)

    def arc_file(self, ext):
        return os.path.join(self.arc_dir, 'example.' + ext)

    def __test_ext(self, ext):
        extract = get_extract_func(ext)
        extract(self.arc_file(ext), self.target)
        assert os.listdir(os.path.dirname(self.expect_file)) == ['example.txt']

    def test_rar(self):
        self.__test_ext('rar')

    @mock.patch('pakit.shell.sub')
    def test_rar_no_command(self, mock_sub):
        mock_sub.side_effect = PakitCmdError('No cmd.')
        with pytest.raises(PakitCmdError):
            self.__test_ext('rar')

    def test_tb2(self):
        self.__test_ext('tb2')

    def test_tbz(self):
        self.__test_ext('tbz')

    def test_tbz2(self):
        self.__test_ext('tbz2')

    def test_tgz(self):
        self.__test_ext('tgz')

    def test_txz(self):
        self.__test_ext('txz')

    def test_tar_bz2(self):
        self.__test_ext('tar.bz2')

    def test_tar_gz(self):
        self.__test_ext('tar.gz')

    def test_tar_xz(self):
        self.__test_ext('tar.xz')

    def test_zip(self):
        self.__test_ext('zip')

    def test_7z(self):
        self.__test_ext('7z')


class TestArchive(object):
    def setup(self):
        self.config = tc.env_setup()
        self.test_dir = os.path.join(self.config.get('paths.source'), 'tmux')
        self.archive = Archive(tc.TMUX, target=self.test_dir,
                               hash='977871e7433fe054928d86477382bd5f6794dc3d')

    def teardown(self):
        tc.delete_it(self.archive.arc_file)
        tc.delete_it(self.test_dir)

    def test__str__(self):
        expect = 'Archive: ' + self.archive.uri
        assert str(self.archive) == expect

    def test_download_remote(self):
        self.archive.uri = tc.TAR
        self.archive.download()
        assert os.path.exists(self.archive.arc_file)

    def test_download_local(self):
        self.archive.download()
        assert os.path.exists(self.archive.arc_file)

    def test_download_bad_hash(self):
        self.archive = Archive(tc.TMUX, target=self.test_dir, hash='bad hash')
        with pytest.raises(PakitError):
            self.archive.download()

    def test_extract(self):
        self.archive.get_it()
        assert os.path.exists(self.test_dir)
        assert len(os.listdir(self.test_dir)) != 0
        assert os.path.join(self.test_dir, 'README')

    def test_hash(self):
        self.archive.download()
        assert self.archive.src_hash == self.archive.actual_hash

    def test_clean(self):
        self.archive.download()
        self.archive.clean()
        assert not os.path.exists(self.archive.arc_file)


class TestGit(object):
    def setup(self):
        self.config = tc.env_setup()
        self.test_dir = os.path.join(self.config.get('paths.source'), 'git')
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
        assert self.repo.src_hash == '20d62b4e3f88c4e38fead73cc4030d8bb44c7259'

    def test_update(self):
        self.repo.branch = 'master'
        self.repo.download()

        # Lop off history to ensure updateable
        latest_hash = self.repo.src_hash
        cmd = Command('git reset --hard HEAD~3', self.repo.target)
        cmd.wait()
        assert self.repo.src_hash != latest_hash
        self.repo.update()
        assert self.repo.src_hash == latest_hash

    def test__str__(self):
        uri = 'https://github.com/user/repo'
        tag = 'default'
        repo_tag = Git(uri, tag=tag)
        repo_branch = Git(uri, branch=tag)

        print()
        print(str(repo_tag))
        print(str(repo_branch))

        expect = 'Git: branch: {0}, uri: {1}'.format(tag, uri)
        assert str(repo_branch) == expect
        assert str(repo_tag) == 'Git: tag: {0}, uri: {1}'.format(tag, uri)


class TestHg(object):
    def setup(self):
        self.config = tc.env_setup()
        self.test_dir = os.path.join(self.config.get('paths.source'), 'hg')
        hg_url = os.path.join(tc.STAGING, 'hg')
        self.repo = Hg(hg_url, target=self.test_dir, tag='0.2')

    def teardown(self):
        tc.delete_it(self.test_dir)

    def test_hash(self):
        assert self.repo.src_hash == '80:a6ec48f03985'

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
        assert self.repo.src_hash == '14:d390b5e27191'

    def test_update(self):
        self.repo.branch = 'default'
        self.repo.download()

        # Lop off history to ensure updateable
        latest_hash = self.repo.src_hash
        cmd = Command('hg strip tip', self.repo.target)
        cmd.wait()
        assert self.repo.src_hash != latest_hash
        self.repo.update()
        assert self.repo.src_hash == latest_hash


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
            with open('dummy/hello', 'wb') as fout:
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

    def test_cmd_failed(self):
        cmd = Command('false')
        with pytest.raises(PakitCmdError):
            cmd.wait()

    def test_cmd_timeout(self):
        cmd = Command('sleep 10')
        with pytest.raises(PakitCmdTimeout):
            cmd.wait(2)

    def test_prev_cmd_stdin(self):
        cmd = Command('echo -e "Hello\nGoodbye!"')
        cmd.wait()
        cmd2 = Command('grep "ood"', prev_cmd=cmd)
        cmd2.wait()
        assert cmd2.output() == ['Goodbye!']
