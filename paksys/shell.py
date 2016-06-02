"""
All code related to running system commands.

Command: Class to run arbitrary system commands.
Archive: Used to fetch a source archive.
Git: Used to fetch a git repository.
Hg: Used to fetch a mercurial repository.
"""
from __future__ import absolute_import
from abc import abstractmethod, abstractproperty
import glob
import inspect
import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from tempfile import NamedTemporaryFile as TempFile
import threading
import time

import pakit.conf
from pakit.ifaces import Fetchable
from pakit.exc import (
    PakitError, PakitCmdError, PakitCmdTimeout, PakitLinkError
)


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


def vcs_factory(uri, **kwargs):
    """
    Given a uri, match it with the right VersionRepo subclass.

    Args:
        uri: The version control URI.

    Returns:
        The instantiated VersionRepo subclass. Any kwargs, are
        passed along to the constructor of the subclass.

    Raises:
        PakitError: The URI is not supported.
    """
    subclasses = []
    for _, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and issubclass(obj, VersionRepo):
            subclasses.append(obj)
    subclasses.remove(VersionRepo)

    for cls in subclasses:
        if cls.valid_uri(uri):
            return cls(uri, **kwargs)

    raise PakitError('Unssupported URI: ' + uri)


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


class VersionRepo(Fetchable):
    """
    Base class for all version control support.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        super(VersionRepo, self).__init__(uri, kwargs.get('target', None))
        tag = kwargs.get('tag', None)
        if tag is not None:
            self.__tag = tag
            self.on_branch = False
        else:
            self.__tag = kwargs.get('branch', None)
            self.on_branch = True

    def __enter__(self):
        """
        Guarantees that the repo is downloaded and on the right commit.
        """
        if not self.ready:
            self.clean()
            self.download()
        else:
            self.checkout()
            if self.on_branch:
                self.update()

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        self.reset()

    def __str__(self):
        if self.on_branch:
            tag = 'HEAD' if self.tag is None else self.tag
            tag = 'branch: ' + tag
        else:
            tag = 'tag: ' + self.tag
        return '{name}: {tag}, uri: {uri}'.format(
            name=self.__class__.__name__, uri=self.uri, tag=tag)

    @property
    def branch(self):
        """
        A branch of the repository.
        """
        return self.__tag

    @branch.setter
    def branch(self, new_branch):
        """
        Set the branch to checkout from the repository.
        """
        self.on_branch = True
        self.__tag = new_branch

    @property
    def tag(self):
        """
        A revision or tag of the repository.
        """
        return self.__tag

    @tag.setter
    def tag(self, new_tag):
        """
        Set the tag to checkout from the repository.
        """
        self.on_branch = False
        self.__tag = new_tag

    @abstractproperty
    def ready(self):
        """
        Returns true iff the repository is available and the
        right tag or branch is checked out.
        """
        raise NotImplementedError

    @abstractproperty
    def src_hash(self):
        """
        The hash of the current commit.
        """
        raise NotImplementedError

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        raise NotImplementedError

    @abstractmethod
    def checkout(self):
        """
        Equivalent to git checkout for the version system.
        """
        raise NotImplementedError

    @abstractmethod
    def download(self):
        """
        Download the repository to the target.
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """
        Clears away all build files from repo.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        raise NotImplementedError


class Git(VersionRepo):
    """
    Fetch a git repository from the given URI.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    If neither provided, will checkout 'master' branch.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        """
        Constructor for a git repository.
        By default checks out the default branch.
        The *branch* and *tag* kwargs are mutually exclusive.

        Args:
            uri: The URI that hosts the repository.

        Kwargs:
            branch: A branch to checkout and track.
            tag: Any fixed tag like a revision or tagged commit.
            target: Path on system to clone to.
        """
        super(Git, self).__init__(uri, **kwargs)
        if self.on_branch and kwargs.get('tag') is None:
            self.branch = 'master'

    @property
    def ready(self):
        """
        Returns true iff the repository is available and
        the right tag or branch is checked out.
        """
        if not os.path.exists(os.path.join(self.target, '.git')):
            return False

        cmd = Command('git remote show origin', self.target)
        return self.uri in cmd.output()[1]

    @property
    def src_hash(self):
        """
        Return the current hash of the repository.
        """
        with self:
            cmd = Command('git rev-parse HEAD', self.target)
            return cmd.output()[0]

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        try:
            cmd = Command('git ls-remote ' + uri)
            return cmd.rcode == 0
        except PakitError:
            return False

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('git checkout ' + self.tag, self.target)

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-b ' + self.tag
        Command('git clone --recursive {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))

    def reset(self):
        """
        Clears away all build files from repo.
        """
        Command('git clean -f', self.target)

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        Command('git fetch origin +{0}:new{0}'.format(self.branch),
                self.target)
        Command('git merge --ff-only new' + self.branch, self.target)


class Hg(VersionRepo):
    """
    Fetch a mercurial repository from the given URI.

    When a 'tag' is set, check out a specific revision of the repository.
    When a 'branch' is set, checkout out the latest commit on the branch of
    the repository.
    If neither provided, will checkout 'default' branch.
    These two options are mutually exclusive.

    Attributes:
        branch: A branch to checkout during clone.
        src_hash: The hash of the current commit.
        tag: A tag to checkout during clone.
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    def __init__(self, uri, **kwargs):
        """
        Constructor for a mercurial repository.
        By default checks out the default branch.
        The *branch* and *tag* kwargs are mutually exclusive.

        Args:
            uri: The URI that hosts the repository.

        Kwargs:
            branch: A branch to checkout and track.
            tag: Any fixed tag like a revision or tagged commit.
            target: Path on system to clone to.
        """
        super(Hg, self).__init__(uri, **kwargs)
        if self.on_branch and kwargs.get('tag') is None:
            self.branch = 'default'

    @property
    def ready(self):
        """
        Returns true iff the repository is available and the
        right tag or branch is checked out.
        """
        if not os.path.exists(os.path.join(self.target, '.hg')):
            return False

        found = False
        with open(os.path.join(self.target, '.hg', 'hgrc')) as fin:
            for line in fin:
                if self.uri in line:
                    found = True
                    break

        return found

    @property
    def src_hash(self):
        """
        Return the current hash of the repository.
        """
        with self:
            cmd = Command('hg identify', self.target)
            return cmd.output()[0].split()[0]

    @staticmethod
    def valid_uri(uri):
        """
        Validate that the supplied uri is handled by this class.

        Returns:
            True if the URI is valid for this class, else False.
        """
        try:
            cmd = Command('hg identify ' + uri)
            return cmd.rcode == 0
        except PakitError:
            return False

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('hg update ' + self.tag, self.target)

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-u ' + self.tag
        Command('hg clone {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))

    def reset(self):
        """
        Clears away all build files from repo.
        """
        cmd = Command('hg status -un', self.target)
        for path in cmd.output():
            os.remove(os.path.join(self.target, path))

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        Command('hg pull -b ' + self.branch, self.target)
        Command('hg update', self.target)


def cmd_kwargs(kwargs):
    """
    Helper, process kwargs given and return ones to pass
    to subprocess.Popen.
    Will insert default kwargs where appropriate.
    """
    if kwargs.get('prev_cmd'):
        kwargs['stdin'] = open(kwargs.pop('prev_cmd').stdout.name, 'r')
    else:
        kwargs['stdin'] = None
    if kwargs.get('stdout') is None:
        kwargs['stdout'] = TempFile(mode='wb', delete=False,
                                    dir=pakit.conf.TMP_DIR,
                                    prefix='cmd', suffix='.log')
    if kwargs.get('stderr') is None:
        kwargs['stderr'] = subprocess.STDOUT
    if kwargs.get('preexec_fn') is None:
        kwargs['preexec_fn'] = os.setsid
    if kwargs.get('env'):
        new_env = os.environ.copy()
        new_env.update(kwargs['env'])
        kwargs['env'] = new_env
    else:
        kwargs['env'] = None
    if kwargs.get('wait') is None:
        kwargs['wait'] = True


class Command(object):
    """
    Execute a command on the host system.

    Once the constructor returns, the command is running.
    At that point, either wait for it to complete or go about your business.
    The process and all children will be part of the same process group,
    this allows for easy termination via signals.

    Attributes:
        alive: True only if the command is still running.
        rcode: When the command finishes, is the return code.
    """
    def __init__(self, cmd, cwd=None, **kwargs):
        """
        Run a command on the system.

        Note: Don't use '|' or '&', instead execute commands
        one after another & supply prev_cmd.

        Args:
            cmd: A string that you would type into the shell.
                If shlex.split would not correctly split the line
                then pass a list.
            cwd: Change to this directory before executing.

        Kwargs:
            env: A dictionary of environment variables to change.
                For instance, env={'HOME': '/tmp'} would change
                HOME variable for the duration of the Command.
            prev_cmd: Read the stdout of this command for stdin.
            wait: Wait for command before returning, default True.

        Raises:
            PakitCmdError: The command could not find command on system
                or the cwd did not exist during subprocess execution.
        """
        super(Command, self).__init__()

        kwargs['cwd'] = cwd
        cmd_kwargs(kwargs)
        if isinstance(cmd, list):
            self.cmd = cmd
        else:
            self.cmd = shlex.split(cmd)
        if self.cmd[0].find('./') != 0:
            self.cmd.insert(0, '/usr/bin/env')

        self.cmd_dir = kwargs.get('cwd')
        self.stdout = kwargs.get('stdout')

        logging.debug('CMD START: %s', self)
        try:
            wait = kwargs.pop('wait')
            self._proc = subprocess.Popen(self.cmd, **kwargs)
            if wait:
                self.wait()
        except OSError as exc:
            if self.cmd_dir and not os.path.exists(self.cmd_dir):
                raise PakitCmdError('Command directory does not exist: ' +
                                    self.cmd_dir)
            else:
                raise PakitCmdError('General OSError:\n' + str(exc))

    def __del__(self):
        """
        When the command object is garbage collected:
            - Terminate processes if still running.
            - Write the entire output of the command to the log.
        """
        try:
            if self.alive:
                self.terminate()  # pragma: no cover
            self.stdout.close()
            prefix = '\n    '
            msg = prefix + prefix.join(self.output())
            logging.debug("CMD LOG: %s%s", self, msg)
        except AttributeError:
            logging.error('Could not execute command: ' + str(self))
        except (IOError, OSError) as exc:
            logging.error(exc)

    def __str__(self):
        return 'Command: {0}, {1}'.format(self.cmd, self.cmd_dir)

    @property
    def alive(self):
        """
        The command is still running.
        """
        return self._proc.poll() is None

    @property
    def rcode(self):
        """
        The return code of the command.
        """
        return self._proc.returncode

    def output(self, last_n=0):
        """
        The output of the run command.

        Args:
            last_n: Return last n lines from output, default all output.

        Returns:
            A list of lines from the output of the command.
        """
        if self._proc is None or not os.path.exists(self.stdout.name):
            return []  # pragma: no cover

        # TODO: Handle encoding better?
        with open(self.stdout.name, 'rb') as out:
            lines = [line.strip().decode('utf-8', 'ignore')
                     for line in out.readlines()]

        return lines[-last_n:]

    def terminate(self):
        """
        Terminates the subprocess running the command and all
        children spawned by the command.

        On return, they are all dead.
        """
        if self.alive:
            os.killpg(self._proc.pid, signal.SIGTERM)
            self._proc.wait()

    def wait(self, timeout=None):
        """
        Block here until the command is done.

        Args:
            timeout: If no stdout for this interval
                     terminate the command and raise error.

        Raises:
            PakitCmdTimeout: When stdout stops getting output for max_time.
            PakitCmdError: When return code is not 0.
        """
        if not timeout:
            timeout = pakit.conf.CONFIG.get('pakit.command.timeout')

        thrd = threading.Thread(target=(lambda proc: proc.wait()),
                                args=(self._proc,))
        thrd.start()
        thread_not_started = True
        while thread_not_started:
            try:
                thrd.join(0.1)
                thread_not_started = False
            except RuntimeError:  # pragma: no cover
                pass

        while self._proc.poll() is None:
            thrd.join(0.5)
            interval = time.time() - os.path.getmtime(self.stdout.name)
            if interval > timeout:
                self.terminate()
                raise PakitCmdTimeout('\n'.join(self.output(10)))

        if self.rcode != 0:
            raise PakitCmdError('\n'.join(self.output(10)))
