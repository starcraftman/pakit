"""
All code related to running system commands.

Command: Class to run arbitrary system commands.
Archive: Used to fetch a source archive.
Git: Used to fetch a git repository.
Hg: Used to fetch a mercurial repository.
"""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod, abstractproperty

import atexit
import glob
import logging
import os
import shlex
import shutil
import signal
import subprocess as sub
import sys
from tempfile import NamedTemporaryFile as TempFile
import threading as thr
import time

import hashlib
import tarfile
try:
    import urllib2 as ulib
except ImportError:
    import urllib.request as ulib  # pylint: disable=E0611,F0401
import zipfile

import pakit.conf
from pakit.exc import PakitError, PakitCmdError, PakitCmdTimeout

EXTS = None
TMP_DIR = '/tmp/pakit'


def wrap_extract(extract_func):
    """
    A decorator that handles some boiler plate between
    extract functions.

    Condition: extract_func must extract the folder with source
    into the tmp_dir. Rest is handled automatically.
    """
    def inner(filename, target):
        """
        Inner part of decorator.
        """
        tmp_dir = os.path.join(TMP_DIR, os.path.basename(filename))
        extract_func(filename, tmp_dir)
        extracted = glob.glob(os.path.join(tmp_dir, '*'))[0]
        shutil.move(extracted, target)
        os.rmdir(tmp_dir)
    return inner


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
            Command(cmd).wait()
            success = True
        except (OSError, PakitCmdError):
            pass
        finally:
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass

    if not success:
        raise PakitCmdError('Need `rar` or `unrar` command to extract: '
                            + filename)


def extract_tb2(filename, tmp_dir):
    """
    Alias for tar.bz2
    """
    extract_tar_bz2(filename, tmp_dir)


def extract_tbz(filename, tmp_dir):
    """
    Alias for tar.bz2
    """
    extract_tar_bz2(filename, tmp_dir)


def extract_tbz2(filename, tmp_dir):
    """
    Alias for tar.bz2
    """
    extract_tar_bz2(filename, tmp_dir)


def extract_tgz(filename, tmp_dir):
    """
    Alias for tar.gz
    """
    extract_tar_gz(filename, tmp_dir)


def extract_txz(filename, tmp_dir):
    """
    Alias for tar.xz
    """
    extract_tar_xz(filename, tmp_dir)


def extract_tar_bz2(filename, tmp_dir):
    """
    Extracts a tar.bz2 archive
    """
    extract_tar_gz(filename, tmp_dir)


@wrap_extract
def extract_tar_gz(filename, tmp_dir):
    """
    Extracts a tar.gz archive to a temp dir
    """
    tarf = tarfile.open(filename)
    tarf.extractall(tmp_dir)


@wrap_extract
def extract_tar_xz(filename, tmp_dir):
    """
    Extracts a tar.xz archive to a temp dir
    """
    try:
        os.makedirs(tmp_dir)
    except OSError:  # pragma: no cover
        pass
    try:
        # Note: Requires GNU tar 1.22, released 2009
        Command('tar -C {0} -xvf {1}'.format(tmp_dir, filename)).wait()
    except (OSError, PakitCmdError):
        raise PakitCmdError('Need `tar --version` >= 1.22 to extract: '
                            + filename)
    finally:
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


@wrap_extract
def extract_7z(filename, tmp_dir):
    """
    Extracts a 7z archive
    """
    try:
        Command('7z x -o{tmp} {file}'.format(file=filename,
                                             tmp=tmp_dir)).wait()
    except (OSError, PakitCmdError):
        raise PakitCmdError('Need `7z` to extract: ' + filename)
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass


def find_arc_name(uri):
    """
    Given a URI, extract the filename of the archive by locating the extension.

    For examle, if uri = 'somesite.com/files/archive.tar.gz' this function
    will return 'archive.tar.gz'. The extension of the archive must be in EXTS.

    Args:
        uri: A URI that stores the archive.

    Returns:
        A tuple of archive name & extension.
    """
    right = -1
    ext = None
    for ext in EXTS:
        ext = '.' + ext
        right = uri.rfind(ext)
        if right != -1:
            right += len(ext)
            left = uri.rfind('/', 0, right) + 1
            break

    if right == -1:
        raise PakitError('Could not determine archive name.')

    return (uri[left:right], ext[1:])


def get_extract_func(ext):
    """
    Get the right extract function given an extension.

    Args:
        ext: The extension of the archive, not including the period.
            For example, zip or tar.gz

    Returns:
        The function of the form extract(filename, target).

    Raises:
        PakitError: The extension can not be extracted.
    """
    this_module = sys.modules[__name__]
    try:
        return getattr(this_module, 'extract_' + ext.replace('.', '_'))
    except AttributeError:
        raise PakitError('Unsupported Archive Format: extension ' + ext)


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


class Fetchable(object):
    """
    Extablishes an abstract interface for fetching source code.

    Subclasses are destined for Recipe.repos to be used to retrieve source
    from the wild.

    Attributes:
        target: The folder the source code should end up in.
        uri: The location of the source code.
    """
    __metaclass__ = ABCMeta

    def __init__(self, uri, target):
        self.target = target
        self.uri = uri

    @abstractmethod
    def __enter__(self):
        """
        Guarantees that source is available at target
        """
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Handles errors as needed
        """
        raise NotImplementedError

    @abstractproperty
    def ready(self):
        """
        True iff the source code is available at target
        """
        raise NotImplementedError

    @abstractproperty
    def src_hash(self):
        """
        A hash that identifies the source snapshot
        """
        raise NotImplementedError

    def clean(self):
        """
        Purges the source tree from the system
        """
        Command('rm -rf ' + self.target).wait()

    @abstractmethod
    def download(self):
        """
        Retrieves code from the remote, may require additional steps
        """
        raise NotImplementedError


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
            filename: If filename detection fails,
                pass in a name with right extension.
            hash: The sha256 hash of the archive.
            target: Path on system to extract to.
        """
        super(Archive, self).__init__(uri, kwargs.get('target', None))

        filename = kwargs.get('filename')
        if filename:
            self.filename = filename
            ext = filename[filename.find('.') + 1:]
        else:
            self.filename, ext = find_arc_name(self.uri)
        self.__src_hash = kwargs.get('hash', '')
        self.__extract = get_extract_func(ext)

    def __enter__(self):
        """
        Guarantees that source is available at target
        """
        if self.ready:
            return

        logging.info('Downloading %s', self.arc_file)
        self.download()
        logging.info('Extracting %s to %s', self.arc_file, self.target)
        self.__extract(self.arc_file, self.target)
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
            resp = ulib.urlopen(self.uri)
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


class VersionRepo(Fetchable):
    """
    Base class for all version control downloaders.

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

    @abstractmethod
    def checkout(self):
        """
        Equivalent to git checkout for the version syste.
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
        cmd.wait()
        return self.uri in cmd.output()[1]

    @property
    def src_hash(self):
        """
        Return the current hash of the repository.
        """
        with self:
            cmd = Command('git log -1 ', self.target)
            cmd.wait()
            hash_line = cmd.output()[0]
            return hash_line.split()[-1]

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('git checkout ' + self.tag, self.target).wait()

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-b ' + self.tag
        cmd = Command('git clone --recursive {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()

    def reset(self):
        """
        Clears away all build files from repo.
        """
        Command('git clean -f', self.target).wait()

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        cmd = Command('git fetch origin +{0}:new{0}'.format(self.branch),
                      self.target)
        cmd.wait()
        cmd = Command('git merge --ff-only new' + self.branch, self.target)
        cmd.wait()


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
            cmd = Command('hg parents', self.target)
            cmd.wait()
            hash_line = cmd.output()[0]
            return hash_line.split()[-1]

    def checkout(self):
        """
        Checkout the right tag or branch.
        """
        Command('hg update ' + self.tag, self.target).wait()

    def download(self):
        """
        Download the repository to the target.
        """
        tag = '' if self.tag is None else '-u ' + self.tag
        cmd = Command('hg clone {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()

    def reset(self):
        """
        Clears away all build files from repo.
        """
        cmd = Command('hg status -un', self.target)
        cmd.wait()
        for path in cmd.output():
            os.remove(os.path.join(self.target, path))

    def update(self):
        """
        Fetches latest commit when branch is set.
        """
        cmd = Command('hg pull -b ' + self.branch, self.target)
        cmd.wait()
        cmd = Command('hg update', self.target)
        cmd.wait()


# TODO: Make this unecessary
@atexit.register
def cmd_cleanup():
    """
    Cleans up any command stdout files left over,
    """
    for filename in glob.glob(os.path.join(TMP_DIR, 'cmd*')):
        try:
            os.remove(filename)
        except OSError:
            logging.error('Could not delete file %s.', filename)
            raise


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
    def_timeout = None

    def __init__(self, cmd, cmd_dir=None, prev_cmd=None):
        """
        Run a command on the system.

        Note: Don't use '|' or '&', instead execute commands
        one after another & supply prev_cmd.

        Args:
            cmd: A string that you would type into the shell.
                If shlex.split would not correctly split the line
                then pass a list.
            cmd_dir: Change to this directory before executing.
            prev_cmd: Read the stdout of this command for stdin.

        Raises:
            PakitCmdError: Usually could not find command on system.
        """
        super(Command, self).__init__()
        if isinstance(cmd, list):
            self._cmd = cmd
        else:
            self._cmd = shlex.split(cmd)
        self._cmd_dir = cmd_dir
        stdin = None
        if prev_cmd:
            stdin = open(prev_cmd.stdout.name, 'r')

        logging.debug('CMD START: %s', self)
        try:
            self.stdout = TempFile(mode='wb', delete=False, dir=TMP_DIR,
                                   prefix='cmd', suffix='.log')
            self._proc = sub.Popen(
                self._cmd, cwd=self._cmd_dir, preexec_fn=os.setsid,
                stdin=stdin, stdout=self.stdout, stderr=sub.STDOUT
            )
        except OSError:
            if cmd_dir and not os.path.exists(cmd_dir):
                raise PakitCmdError('Command directory does not exist: '
                                    + self._cmd_dir)
            else:
                raise PakitCmdError('Command not available: ' + self._cmd[0])

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
        except (AttributeError, IOError, OSError) as exc:
            logging.error(exc)

    def __str__(self):
        return 'Command: {0}, {1}'.format(self._cmd, self._cmd_dir)

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

        with open(self.stdout.name, 'r') as out:
            lines = [line.rstrip() for line in out.readlines()]

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
            max_time: If stdout receives no text for this interval,
                terminate the command and raise error.

        Raises:
            PakitCmdTimeout: When stdout stops getting output for max_time.
            PakitCmdError: When return code is not 0.
        """
        if not timeout:
            timeout = pakit.conf.CONFIG.get('pakit.command.timeout')

        thrd = thr.Thread(target=(lambda proc: proc.wait()),
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

# Placed here on purpose, pick up any extract funcs before me
EXTS = [func.replace('extract_', '').replace('_', '.') for func
        in dir(sys.modules[__name__]) if func.find('extract_') == 0]
