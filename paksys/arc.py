"""
Any code related to handling source archives.
"""
from __future__ import absolute_import

import functools
import glob
import hashlib
import logging
import os
import shutil
import sys
import tempfile
from tempfile import NamedTemporaryFile as TempFile
# pylint: disable=import-error
try:
    import urllib2 as ulib
except ImportError:  # pragma: no cover
    import urllib.request as ulib  # pylint: disable=no-name-in-module
# pylint: enable=import-error
import zipfile

import pakit.conf
from pakit.exc import PakitCmdError, PakitError
from pakit.ifaces import Fetchable
from paksys.cmd import Command


EXT_FUNCS = {
    'application/x-7z-compressed': 'extract_7z',
    'application/x-rar': 'extract_rar',
    'application/gzip': 'extract_tar_gz',
    'application/x-gzip': 'extract_tar_gz',
    'application/x-bzip2': 'extract_tar_gz',
    'application/x-tar': 'extract_tar_gz',
    'application/x-xz': 'extract_tar_xz',
    'application/zip': 'extract_zip',
}


class Archive(Fetchable):
    """
    Retrieve an archive from a remote URI and extract it to target.

    Supports any extension that has an extract function in this module
    of the form `extract_ext`. For example, if given a zip will use the
    extract_zip function.

    Attributes:
        actual_hash: The actual sha256 hash of the archive.
        filename: The filename of the archive.
        src_hash: The expected sha256 hash of the archive.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        """
        Constructor for Archive. *uri* and *hash* are required.

        Args:
            uri: The URI to retrieve the archive from.

        Kwargs:
            filename: The filename to use, else a tempfile will be used.
            hash: The sha256 hash of the archive.
            target: Path on system to extract to.
        """
        super(Archive, self).__init__(uri, kwargs.get('target', None))

        self.__src_hash = kwargs.get('hash', '')
        self.filename = kwargs.get('filename')
        if self.filename is None:
            self.__tfile = TempFile(mode='wb', delete=False,
                                    dir=pakit.conf.TMP_DIR,
                                    prefix='arc')
            self.filename = self.__tfile.name

    def __enter__(self):
        """
        Guarantees that source is available at target
        """
        if self.ready:
            return

        logging.info('Downloading %s', self.arc_file)
        self.download()
        logging.info('Extracting %s to %s', self.arc_file, self.target)
        get_extract_func(self.arc_file)(self.arc_file, self.target)
        with open(os.path.join(self.target, '.archive'), 'wb') as fout:
            fout.write(self.src_hash.encode())
        os.remove(self.arc_file)

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        self.clean()

    def __str__(self):
        return '{name}: {uri}'.format(name=self.__class__.__name__,
                                      uri=self.uri)

    @property
    def arc_file(self):
        """
        The path to the downloaded archive.
        """
        target = self.target
        if target.find('./') == 0:
            target = target.replace('./', '')
        return os.path.join(os.path.dirname(target), self.filename)

    @property
    def ready(self):
        """
        True iff the source code is available at target
        """
        try:
            with open(os.path.join(self.target, '.archive'), 'rb') as fin:
                file_hash = fin.readlines()[0].decode()
            return file_hash == self.src_hash
        except IOError:
            return False

    @property
    def src_hash(self):
        """
        The expected hash of the archive.
        """
        return self.__src_hash

    def actual_hash(self):
        """
        The actual hash of the downloaded archive file.
        """
        arc_clean = False
        if not os.path.exists(self.arc_file):
            self.download()
            arc_clean = True

        hash_str = hash_archive(self.arc_file)

        if arc_clean:
            os.remove(self.arc_file)
        return hash_str

    def clean(self):
        """
        Guarantee no trace of archive file or source target.
        """
        try:
            os.remove(self.arc_file)
        except OSError:
            pass
        super(Archive, self).clean()

    def download(self):
        """
        Retrieves the archive from the remote URI.

        If the URI is a local file, simply copy it.
        """
        if not os.path.isfile(self.uri):
            resp = ulib.urlopen(self.uri, timeout=30)
            with open(self.arc_file, 'wb') as fout:
                fout.write(resp.read())
        elif self.uri != self.arc_file:
            shutil.copy(self.uri, self.arc_file)

        arc_hash = self.actual_hash()
        if arc_hash != self.src_hash:
            self.clean()
            raise PakitError('Hash mismatch on archive.\n  Expected: {exp}'
                             '\n  Actual: {act}'.format(exp=self.src_hash,
                                                        act=arc_hash))


def wrap_extract(extract_func):
    """
    A decorator that handles some boiler plate between
    extract functions.

    Condition: extract_func must extract the folder with source
    into the tmp_dir. Rest is handled automatically.
    """
    @functools.wraps(extract_func)
    def inner(filename, target):
        """
        Inner part of decorator.
        """
        tmp_dir = tempfile.mkdtemp(dir=pakit.conf.TMP_DIR)
        extract_func(filename, tmp_dir)
        extracted = glob.glob(os.path.join(tmp_dir, '*'))[0]
        shutil.move(extracted, target)
        os.rmdir(tmp_dir)
    return inner


@wrap_extract
def extract_7z(filename, tmp_dir):
    """
    Extracts a 7z archive
    """
    try:
        Command('7z x -o{tmp} {file}'.format(file=filename,
                                             tmp=tmp_dir))
    except (OSError, PakitCmdError):
        raise PakitCmdError('Need `7z` to extract: ' + filename)
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass


@wrap_extract
def extract_rar(filename, tmp_dir):
    """
    Extracts a rar archive
    """
    success = False
    cmd_str = 'rar x {file} {tmp}'.format(file=filename, tmp=tmp_dir)
    for cmd in [cmd_str, 'un' + cmd_str]:
        try:
            os.makedirs(tmp_dir)
            Command(cmd)
            success = True
        except (OSError, PakitCmdError):
            pass
        finally:
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass

    if not success:
        raise PakitCmdError('Need `rar` or `unrar` command to extract: ' +
                            filename)


@wrap_extract
def extract_tar_gz(filename, tmp_dir):
    """
    Extracts any combination of tar, gz, bz2 to a temp dir
    """
    Command('tar -C {0} -xf {1}'.format(tmp_dir, filename))


@wrap_extract
def extract_tar_xz(filename, tmp_dir):
    """
    Extracts a tar.xz archive to a temp dir
    """
    tar_file = filename.split('.')
    tar_file = tar_file[0:-2] if 'tar' in tar_file else tar_file[0:-1]
    tar_file = os.path.join(os.path.dirname(filename),
                            '.'.join(tar_file + ['tar']))
    try:
        os.makedirs(tmp_dir)
    except OSError:  # pragma: no cover
        pass
    try:
        Command('xz --keep --decompress ' + filename)
        Command('tar -C {0} -xf {1}'.format(tmp_dir, tar_file))
    except (OSError, PakitCmdError):
        raise PakitCmdError('Need commands `xz` and `tar` to extract: ' +
                            filename)
    finally:
        os.remove(tar_file)
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass


@wrap_extract
def extract_zip(filename, tmp_dir):
    """
    Extracts a zip archive
    """
    zipf = zipfile.ZipFile(filename)
    zipf.extractall(tmp_dir)


def get_extract_func(arc_path):
    """
    Check mimetype of archive to select extraction method.

    Args:
        arc_path: The absolute path to an archive.

    Returns:
        The function of the form extract(filename, target).

    Raises:
        PakitError: Could not determine function from mimetype.
    """
    cmd = Command('file --mime-type ' + arc_path)
    mtype = cmd.output()[0].split()[1]

    if mtype not in EXT_FUNCS.keys():
        raise PakitError('Unsupported Archive: mimetype ' + mtype)

    return getattr(sys.modules[__name__], EXT_FUNCS[mtype])


def hash_archive(archive, hash_alg='sha256'):
    """
    Hash an archive.

    Args:
        archive: Path to an archive.
        hash_alg: Hashing algorithm to use, available algorithms
            are in hashlib.algorithms

    Returns:
        The hex based hash of the archive, using hash_alg.
    """
    hasher = hashlib.new(hash_alg)
    blk_size = 1024 ** 2

    with open(archive, 'rb') as fin:
        block = fin.read(blk_size)
        while block:
            hasher.update(block)
            block = fin.read(blk_size)

    return hasher.hexdigest()
