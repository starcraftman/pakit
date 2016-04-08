"""
Test pakit.shell
"""
from __future__ import absolute_import, print_function
import os
import mock
import pytest

import pakit.conf
from pakit.exc import (
    PakitError, PakitCmdError, PakitCmdTimeout, PakitLinkError
)
import pakit.shell
from pakit.shell import (
    Archive, Dummy, Git, Hg, Command, hash_archive,
    common_suffix, cmd_cleanup, get_extract_func, extract_tar_gz,
    walk_and_link, walk_and_unlink, walk_and_unlink_all, vcs_factory,
    write_config, link_man_pages, unlink_man_pages, user_input,
    reach_github, cmd_kwargs
)
import tests.common as tc


def test_reach_github():
    assert reach_github()


@mock.patch('pakit.shell.Command')
def test_reach_github_fails(mock_cmd):
    mock_cmd.side_effect = PakitError('Fail.')
    assert not reach_github()


def test_user_input(mock_input):
    mock_input.return_value = 'Bye'
    assert user_input('Hello') == 'Bye'


def test_link_man_pages():
    try:
        link_dir = os.path.join(tc.STAGING, 'links')
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'pakit', 'extra')
        fake_man = os.path.join(src, 'test_man.1')

        try:
            os.makedirs(os.path.dirname(fake_man))
        except OSError:
            pass
        with open(fake_man, 'w') as fout:
            fout.write('hello')

        link_man_pages(link_dir)
        assert os.path.islink(os.path.join(link_dir, 'share', 'man', 'man1',
                                           os.path.basename(fake_man)))
    finally:
        tc.delete_it(fake_man)
        tc.delete_it(link_dir)


def test_unlink_man_pages():
    try:
        link_dir = os.path.join(tc.STAGING, 'links')
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'pakit', 'extra')
        fake_man = os.path.join(src, 'test_man.1')

        try:
            os.makedirs(os.path.dirname(fake_man))
        except OSError:
            pass
        with open(fake_man, 'w') as fout:
            fout.write('hello')

        link_man_pages(link_dir)
        unlink_man_pages(link_dir)

        expected_man = os.path.join(link_dir, 'share', 'man', 'man1',
                                    os.path.basename(fake_man))
        assert not os.path.exists(expected_man)
        assert not os.path.exists(os.path.dirname(expected_man))
        assert os.path.isdir(link_dir)
    finally:
        tc.delete_it(fake_man)
        tc.delete_it(link_dir)


def test_get_extract_func():
    assert get_extract_func(tc.TAR_FILE) is extract_tar_gz


def test_get_extract_func_not_found():
    with pytest.raises(PakitError):
        get_extract_func(tc.TEST_CONFIG)


def test_hash_archive_sha256():
    expect_hash = ('795f4b4446b0ea968b9201c25e8c1ef8a6ade710ebca4657dd879c'
                   '35916ad362')
    arc = Archive(tc.TAR_FILE, target='./temp', hash=expect_hash)
    arc.download()
    assert hash_archive(arc.arc_file) == expect_hash
    os.remove(arc.arc_file)


@mock.patch('pakit.shell.shutil')
def test_cmd_cleanup(mock_shutil):
    cmd_cleanup()
    mock_shutil.rmtree.assert_called_with(pakit.conf.TMP_DIR)


def test_common_suffix():
    path1 = os.path.join('/base', 'prefix', 'ag', 'bin')
    path2 = os.path.join('/root', 'base', 'prefix', 'ag', 'bin')
    assert common_suffix(path1, path2) == path1[1:]
    assert common_suffix(path2, path1) == path1[1:]


def test_vcs_factory():
    print(os.listdir('/tmp'))
    repo = vcs_factory(tc.GIT)
    assert isinstance(repo, Git)
    assert repo.uri == tc.GIT


def test_vcs_factory_unsupported():
    with pytest.raises(PakitError):
        vcs_factory(tc.TAR)


class TestWriteConfig(object):
    def setup(self):
        self.old_rdb = pakit.recipe.RDB
        self.old_conf = pakit.conf.CONFIG
        self.conf_file = os.path.join(tc.STAGING, 'conf.yaml')

    def teardown(self):
        tc.delete_it(self.conf_file)
        pakit.conf.CONFIG = self.old_conf
        pakit.recipe.RDB = self.old_rdb

    def test_write_config(self):
        assert not os.path.exists(self.conf_file)
        write_config(self.conf_file)
        assert os.path.exists(self.conf_file)

    def test_write_config_dir(self):
        os.mkdir(self.conf_file)
        with pytest.raises(PakitError):
            write_config(self.conf_file)

    def test_write_config_perms(self):
        with pytest.raises(PakitError):
            write_config('/ttt.yml')


class TestLinking(object):
    def setup(self):
        self.src = os.path.join(tc.STAGING, 'src')
        self.dst = os.path.join(tc.STAGING, 'dst')
        self.subdir = os.path.join(self.src, 'subdir')

        for path in [self.dst, self.subdir]:
            try:
                os.makedirs(path)
            except OSError:
                pass

        self.fnames = [os.path.join(self.src, 'file' + str(num))
                       for num in range(0, 6)]
        self.fnames += [os.path.join(self.subdir, 'file' + str(num))
                        for num in range(0, 4)]
        self.dst_fnames = [fname.replace(self.src, self.dst)
                           for fname in self.fnames]
        for fname in self.fnames:
            with open(fname, 'wb') as fout:
                fout.write('dummy'.encode())

    def teardown(self):
        tc.delete_it(self.src)
        tc.delete_it(self.dst)

    def test_walk_and_link_works(self):
        walk_and_link(self.src, self.dst)
        for fname in self.dst_fnames:
            assert os.path.islink(fname)
            assert os.readlink(fname) == fname.replace(self.dst, self.src)

    def test_walk_and_link_raises(self):
        walk_and_link(self.src, self.dst)
        with pytest.raises(PakitLinkError):
            walk_and_link(self.src, self.dst)

    def test_walk_and_unlink(self):
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)
        assert os.path.exists(self.dst)

    def test_walk_and_unlink_missing(self):
        walk_and_link(self.src, self.dst)
        os.remove(self.dst_fnames[0])
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)
        assert os.path.exists(self.dst)

    def test_walk_and_unlink_mkdirs(self):
        link_file = os.path.join(self.dst, 'NotSymLink')
        with open(link_file, 'w') as fout:
            fout.write('Hello')

        assert os.path.exists(link_file)
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        assert os.path.exists(self.dst)
        assert os.path.exists(link_file)

    def test_walk_and_unlink_all(self):
        walk_and_link(self.src, self.dst)

        not_link = os.path.join(self.dst, 'notlink')
        with open(not_link, 'w') as fout:
            fout.write('Hello')

        walk_and_unlink_all(self.dst, self.src)
        assert os.path.exists(not_link)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)
        assert os.path.exists(self.dst)


class TestExtractFuncs(object):
    def setup(self):
        self.arc_dir = tc.ARCS
        self.target = os.path.join(tc.STAGING, 'extract')
        self.expect_file = os.path.join(self.target, 'example.txt')

    def teardown(self):
        tc.delete_it(self.target)

    def arc_file(self, ext):
        return os.path.join(self.arc_dir, 'example.' + ext)

    def __test_ext(self, ext):
        extract = get_extract_func(self.arc_file(ext))
        extract(self.arc_file(ext), self.target)
        assert os.listdir(os.path.dirname(self.expect_file)) == ['example.txt']

    def test_rar(self):
        self.__test_ext('rar')

    @mock.patch('pakit.shell.subprocess')
    def test_rar_unavailable(self, mock_sub):
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

    @mock.patch('pakit.shell.subprocess')
    def test_tar_xz_unavailable(self, mock_sub):
        mock_sub.side_effect = PakitCmdError('No cmd.')
        with pytest.raises(PakitCmdError):
            self.__test_ext('tar.xz')

    def test_zip(self):
        self.__test_ext('zip')

    def test_7z(self):
        self.__test_ext('7z')

    @mock.patch('pakit.shell.subprocess')
    def test_7z_unavailable(self, mock_sub):
        mock_sub.side_effect = PakitCmdError('No cmd.')
        with pytest.raises(PakitCmdError):
            self.__test_ext('7z')


class TestDummy(object):
    def setup(self):
        self.test_dir = os.path.join(tc.CONF.path_to('source'), 'dummy')
        self.dummy = Dummy(target=self.test_dir)

    def teardown(self):
        tc.delete_it(self.test_dir)

    def test__str__(self):
        assert str(self.dummy) == 'DummyTask: No source code to fetch.'

    def test__with__(self):
        with self.dummy:
            assert self.dummy.ready

    @mock.patch('pakit.shell.Dummy.clean')
    def test__with__fails(self, _):
        os.makedirs(self.dummy.target)
        with pytest.raises(PakitError):
            with self.dummy:
                pass

    def test_download(self):
        with pytest.raises(NotImplementedError):
            self.dummy.download()

    def test_ready(self):
        with self.dummy:
            assert self.dummy.ready
            with open(os.path.join(self.dummy.target, 'file'), 'w') as fout:
                fout.write('Hello world.')
            assert not self.dummy.ready

    def test_src_hash(self):
        assert self.dummy.src_hash == 'dummy_hash'


class TestArchive(object):
    def setup(self):
        self.test_dir = os.path.join(tc.CONF.path_to('source'), 'tmux')
        self.archive = Archive(tc.TAR_FILE, target=self.test_dir,
                               filename=os.path.basename(tc.TAR_FILE),
                               hash='795f4b4446b0ea968b9201c25e8c1ef8a6ade710'
                               'ebca4657dd879c35916ad362')

    def teardown(self):
        tc.delete_it(self.archive.arc_file)
        tc.delete_it(self.test_dir)

    def test__str__(self):
        expect = 'Archive: ' + self.archive.uri
        assert str(self.archive) == expect

    def test_ready(self):
        with self.archive:
            assert self.archive.ready

    def test_with_nested(self):
        with self.archive:
            with self.archive:
                assert self.archive.ready

    def test_filename_argument(self):
        self.archive = Archive(tc.TAR_FILE, target=self.test_dir,
                               filename='file.tar.gz',
                               hash='795f4b4446b0ea968b9201c25e8c1ef8a6ade710'
                               'ebca4657dd879c35916ad362')
        self.archive.download()
        assert os.path.exists(self.archive.arc_file)
        assert os.path.basename(self.archive.arc_file) == 'file.tar.gz'

    def test_download_remote(self):
        self.archive.uri = tc.TAR
        self.archive.download()
        assert os.path.exists(self.archive.arc_file)

    def test_download_local(self):
        self.archive.download()
        assert os.path.exists(self.archive.arc_file)

    def test_download_bad_hash(self):
        self.archive = Archive(tc.TAR_FILE, target=self.test_dir,
                               hash='bad hash')
        with pytest.raises(PakitError):
            self.archive.download()

    def test_extract(self):
        with self.archive:
            assert os.path.exists(self.test_dir)
            assert len(os.listdir(self.test_dir)) != 0
            assert os.path.join(self.test_dir, 'README')

    def test_hash(self):
        assert self.archive.src_hash == self.archive.actual_hash()

    def test_clean(self):
        self.archive.download()
        self.archive.clean()
        assert not os.path.exists(self.archive.arc_file)
        assert not os.path.exists(self.archive.target)

    def test_clean_extracted(self):
        with self.archive:
            self.archive.clean()
            assert not os.path.exists(self.archive.arc_file)
            assert not os.path.exists(self.archive.target)


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
