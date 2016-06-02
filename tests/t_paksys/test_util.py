"""
Test paksys.util
"""
from __future__ import absolute_import, print_function
import os
import mock
import pytest

import pakit.conf
from pakit.exc import PakitError, PakitLinkError
from paksys.util import (
    Dummy, common_suffix, cd_and_call,
    walk_and_link, walk_and_unlink, walk_and_unlink_all,
    write_config, link_man_pages, unlink_man_pages, user_input,
)
import tests.common as tc


def dummy_func(*args, **kwargs):
    return os.getcwd()


class TestCDCall(object):
    def test_does_not_exist(self):
        with pytest.raises(OSError):
            cd_and_call(dummy_func, new_cwd='/zxyaaaa')

    def test_does_exist(self):
        old_cwd = os.getcwd()
        cwd = cd_and_call(dummy_func, new_cwd='/tmp')
        assert cwd == '/tmp'
        assert os.path.exists(cwd)
        assert os.getcwd() == old_cwd

    def test_use_tempd(self):
        old_cwd = os.getcwd()
        cwd = cd_and_call(dummy_func, use_tempd=True)
        assert cwd.find('/tmp/pakit') == 0
        assert not os.path.exists(cwd)
        assert os.getcwd() == old_cwd


def test_user_input(mock_input):
    mock_input.return_value = 'Bye'
    assert user_input('Hello') == 'Bye'


def test_link_man_pages():
    try:
        link_dir = os.path.join(tc.STAGING, 'links')
        src = os.path.join(os.path.dirname(os.path.dirname(tc.TEST_CONFIG)),
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


def test_common_suffix():
    path1 = os.path.join('/base', 'prefix', 'ag', 'bin')
    path2 = os.path.join('/root', 'base', 'prefix', 'ag', 'bin')
    assert common_suffix(path1, path2) == path1[1:]
    assert common_suffix(path2, path1) == path1[1:]


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

    @mock.patch('paksys.util.Dummy.clean')
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
