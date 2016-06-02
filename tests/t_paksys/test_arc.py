"""
test paksys.arc
"""
from __future__ import absolute_import, print_function
import os
import mock
import pytest

from pakit.exc import PakitCmdError, PakitError
from paksys.arc import (
    Archive, hash_archive, get_extract_func, extract_tar_gz
)
import tests.common as tc


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

    @mock.patch('paksys.cmd.subprocess')
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

    @mock.patch('paksys.cmd.subprocess')
    def test_tar_xz_unavailable(self, mock_sub):
        mock_sub.side_effect = PakitCmdError('No cmd.')
        with pytest.raises(PakitCmdError):
            self.__test_ext('tar.xz')

    def test_zip(self):
        self.__test_ext('zip')

    def test_7z(self):
        self.__test_ext('7z')

    @mock.patch('paksys.cmd.subprocess')
    def test_7z_unavailable(self, mock_sub):
        mock_sub.side_effect = PakitCmdError('No cmd.')
        with pytest.raises(PakitCmdError):
            self.__test_ext('7z')


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
