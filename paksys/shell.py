"""
All code related to running system commands.

Command: Class to run arbitrary system commands.
Archive: Used to fetch a source archive.
Git: Used to fetch a git repository.
Hg: Used to fetch a mercurial repository.
"""
from __future__ import absolute_import
import glob
import logging
import os
import shutil
import sys
import tempfile

import pakit.conf
from pakit.ifaces import Fetchable
from pakit.exc import PakitError, PakitLinkError


def cd_and_call(func, new_cwd=None, use_tempd=False, *args, **kwargs):
    """
    Change directory and THEN execute func with *args and **kwargs.
    Regardless of what func does, directory will be returned to original.

    Kwargs:
        new_cwd: The new directory to change to. Ignored if use_tempd set.
        use_tempd: Create a temporary direcory and cd to it.
    """
    old_cwd = os.getcwd()
    if use_tempd:
        new_cwd = tempfile.mkdtemp(prefix='pakit_tmp_')

    try:
        os.chdir(new_cwd)
        return func(*args, **kwargs)
    finally:
        os.chdir(old_cwd)
        if use_tempd:
            shutil.rmtree(new_cwd)


def user_input(msg):
    """
    Get user input, works on python 2 and 3.

    Args:
        msg: The message to print to user.

    Returns:
        Whatever the user typed.
    """
    if sys.version_info < (3, 0):
        return raw_input(msg)
    else:  # pragma: no cover
        return input(msg)  # pylint: disable=bad-builtin


def common_suffix(path1, path2):
    """
    Given two paths, find the largest common suffix.

    Args:
        path1: The first path.
        path2: The second path.
    """
    suffix = []
    parts1 = path1.split(os.path.sep)
    parts2 = path2.split(os.path.sep)

    if len(parts2) < len(parts1):
        parts1, parts2 = parts2, parts1

    while len(parts1) and parts1[-1] == parts2[-1]:
        suffix.insert(0, parts1.pop())
        parts2.pop()

    return os.path.sep.join(suffix)


def walk_and_link(src, dst):
    """
    Recurse down the tree from src and symbollically link
    the files to their counterparts under dst.

    Args:
        src: The source path with the files to link.
        dst: The destination path where links should be made.

    Raises:
        PakitLinkError: When anything goes wrong linking.
    """
    for dirpath, _, filenames in os.walk(src, followlinks=True, topdown=True):
        link_all_files(dirpath, dirpath.replace(src, dst), filenames)


def walk_and_unlink(src, dst):
    """
    Recurse down the tree from src and unlink the files
    that have counterparts under dst.

    Args:
        src: The source path with the files to link.
        dst: The destination path where links should be removed.
    """
    for dirpath, _, filenames in os.walk(src, followlinks=True, topdown=False):
        unlink_all_files(dirpath, dirpath.replace(src, dst), filenames)
    try:
        os.makedirs(dst)
    except OSError:
        pass


def walk_and_unlink_all(link_root, build_root):
    """
    Walk the tree from bottom up and remove all symbolic links
    pointing into the build_root. Cleans up any empty folders.

    Args:
        build_root: The path where all installations are. Any symlink
            pakit makes will have this as a prefix of the target path.
        link_root: All links are located below this folder.
    """
    for dirpath, _, filenames in os.walk(link_root, followlinks=True,
                                         topdown=False):
        to_remove = []
        for fname in filenames:
            abs_file = os.path.join(dirpath, fname)
            if os.path.realpath(abs_file).find(build_root) == 0:
                to_remove.append(fname)

        unlink_all_files(dirpath, dirpath, to_remove)

    try:
        os.makedirs(link_root)
    except OSError:
        pass


def link_all_files(src, dst, filenames):
    """
    From src directory link all filenames into dst.

    Args:
        src: The directory where the source files exist.
        dst: The directory where the links should be made.
        filenames: A list of filenames in src.
    """
    try:
        os.makedirs(dst)
    except OSError:
        pass  # The folder already existed

    for fname in filenames:
        sfile = os.path.join(src, fname)
        dfile = os.path.join(dst, fname)
        try:
            os.symlink(sfile, dfile)
        except OSError:
            msg = 'Could not symlink {0} -> {1}'.format(sfile, dfile)
            logging.error(msg)
            raise PakitLinkError(msg)


def unlink_all_files(_, dst, filenames):
    """
    Unlink all links in dst that are in filenames.

    Args:
        src: The directory where the source files exist.
        dst: The directory where the links should be made.
        filenames: A list of filenames in src.
    """
    for fname in filenames:
        try:
            os.remove(os.path.join(dst, fname))
        except OSError:
            pass  # The link was not there

    try:
        os.rmdir(dst)
    except OSError:
        pass  # Folder probably had files left.


def link_man_pages(link_dir):
    """
    Silently links project man pages into link dir.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(root, 'pakit', 'extra')
    dst = os.path.join(link_dir, 'share', 'man', 'man1')
    try:
        os.makedirs(dst)
    except OSError:
        pass

    for page in glob.glob(os.path.join(src, '*.1')):
        try:
            os.symlink(page, page.replace(src, dst))
        except OSError:  # pragma: no cover
            pass


def unlink_man_pages(link_dir):
    """
    Unlink all man pages from the link directory.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(root, 'pakit', 'extra')
    dst = os.path.join(link_dir, 'share', 'man', 'man1')

    for page in glob.glob(os.path.join(src, '*.1')):
        try:
            os.remove(page.replace(src, dst))
        except OSError:  # pragma: no cover
            pass

    for paths in os.walk(link_dir, topdown=False):
        try:
            os.rmdir(paths[0])
        except OSError:  # pragma: no cover
            pass

    try:
        os.makedirs(link_dir)
    except OSError:  # pragma: no cover
        pass


def write_config(config_file):
    """
    Writes the DEFAULT config to the config file.
    Overwrites the file if present.

    Raises:
        PakitError: File exists and is a directory.
        PakitError: File could not be written to.
    """
    try:
        os.remove(config_file)
    except OSError:
        if os.path.isdir(config_file):
            raise PakitError('Config path is a directory.')

    try:
        config = pakit.conf.Config(config_file)
        config.reset()
        config.write()
    except (IOError, OSError):
        raise PakitError('Failed to write to ' + config.filename)


class Dummy(Fetchable):
    """
    Creates the target directory when invoked.

    This is a dummy repository, useful for testing and when a recipe
    does NOT rely on a source repository or archive.
    """
    def __init__(self, uri=None, **kwargs):
        """
        Constructor for a Dummy repository.
        Target must be specified before entering context.

        Args:
            uri: Default None, serves no purpose.

        Kwargs:
            target: Path that will be created on the system.
        """
        super(Dummy, self).__init__(uri, kwargs.get('target', None))

    def __str__(self):
        return 'DummyTask: No source code to fetch.'

    def __enter__(self):
        """
        Guarantees that source is available at target
        """
        try:
            self.clean()
            os.makedirs(self.target)
        except OSError:
            raise PakitError('Could not create folder: ' + self.target)

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        pass

    @property
    def ready(self):
        """
        True iff the source code is available at target
        """
        return os.path.isdir(self.target) and len(os.listdir(self.target)) == 0

    @property
    def src_hash(self):
        """
        A hash that identifies the source snapshot
        """
        return 'dummy_hash'

    def download(self):
        """
        Retrieves code from the remote, may require additional steps
        """
        raise NotImplementedError
