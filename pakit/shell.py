""" All things shell related, including Command class. """
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
from tempfile import NamedTemporaryFile

import hashlib
import tarfile
try:
    import urllib2 as ulib
except ImportError:
    import urllib.request as ulib  # pylint: disable=E0611,F0401
import zipfile
from pakit.exc import PakitError

EXTS = None
TMP_DIR = '/tmp/pakit'


def extract_tb2(filename, target):
    """ Short hand extension for tar.bz2 """
    extract_tar_bz2(filename, target)


def extract_tbz(filename, target):
    """ Short hand extension for tar.bz2 """
    extract_tar_bz2(filename, target)


def extract_tbz2(filename, target):
    """ Short hand extension for tar.bz2 """
    extract_tar_bz2(filename, target)


def extract_tgz(filename, target):
    """ Short hand extension for tar.gz """
    extract_tar_gz(filename, target)


def extract_tar_bz2(filename, target):
    """ Extracts a tar.bz2 archive """
    extract_tar_gz(filename, target)


def extract_tar_gz(filename, target):
    """ Extracts a tar.gz archive """
    tmp_dir = os.path.join(TMP_DIR, os.path.basename(filename))
    tarf = tarfile.open(filename)
    tarf.extractall(tmp_dir)
    extracted = glob.glob(os.path.join(tmp_dir, '*'))[0]
    shutil.move(extracted, target)


def extract_zip(filename, target):
    """ Extracts a zip archive """
    tmp_dir = os.path.join(TMP_DIR, os.path.basename(filename))
    zipf = zipfile.ZipFile(filename)
    zipf.extractall(tmp_dir)
    extracted = glob.glob(os.path.join(tmp_dir, '*'))[0]
    shutil.move(extracted, target)


def find_arc_name(uri):
    """ Determine & return the archive name & extension. """
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
    """ Returns the associated extract method based on archive extension. """
    this_module = sys.modules[__name__]
    try:
        return getattr(this_module, 'extract_' + ext.replace('.', '_'))
    except AttributeError:
        raise PakitError('Unsupported Archive Format: extension ' + ext)


# TODO: Common interface between Archive & VersionRepo
class Archive(object):
    """ All archives can be supported by this class. """
    def __init__(self, uri, **kwargs):
        self.uri = uri
        self.arc_hash = kwargs.get('hash', '')
        self.target = kwargs.get('target', None)
        self.filename, ext = find_arc_name(self.uri)
        self.__extract = get_extract_func(ext)

    def __str__(self):
        return '{name}: {uri}'.format(name=self.__class__.__name__,
                                      uri=self.uri)

    @property
    def arc_file(self):
        """ The location of the archive. """
        target = self.target
        if target.find('./') == 0:
            target = target.replace('./', '')
        return os.path.join(os.path.dirname(target), self.filename)

    @property
    def cur_hash(self):
        """ Expected hash of the archive. """
        return self.arc_hash

    @property
    def file_hash(self):
        """ For archives, the hash of the archive. """
        # TODO: Support all hashlib.algorithms:
        #   ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
        hasher = hashlib.new('sha1')
        blk_size = 2 ** 10
        with open(self.arc_file, 'rb') as fin:
            block = fin.read(blk_size)
            while block:
                hasher.update(block)
                block = fin.read(blk_size)
            return hasher.hexdigest()

    @property
    def ready(self):
        """ Check folder is not empty. """
        return os.path.exists(self.target) and \
            len(os.listdir(self.target)) != 0

    def clean(self):
        """ Simply purges the source tree. """
        cmd = Command('rm -rf ' + self.target)
        cmd.wait()

    def download(self):
        """ Just download the archive. """
        resp = ulib.urlopen(self.uri)
        with open(self.arc_file, 'wb') as fout:
            fout.write(resp.read())
        if self.file_hash != self.cur_hash:
            raise PakitError('Hash mismatch on archive')

    def get_it(self):
        """ Guarantees the source available. """
        if not self.ready:
            logging.info('Downloading %s', self.arc_file)
            self.download()
            logging.info('Extracting %s to %s', self.arc_file, self.target)
            self.__extract(self.arc_file, self.target)


class VersionRepo(object):
    """ Base class for all version control downloaders.

        uri: The url of the repository.

        Optional Kwargs:
        target:     A path on local disk where it will be cloned.
        branch:     A branch to checkout during clone.
        tag:        A tag to checkout during clone.
    """
    __metaclass__ = ABCMeta

    def __init__(self, uri, **kwargs):
        self.uri = uri
        self.target = kwargs.get('target', None)
        tag = kwargs.get('tag', None)
        if tag is not None:
            self.__tag = tag
            self.on_branch = False
        else:
            self.__tag = kwargs.get('branch', None)
            self.on_branch = True

    def get_it(self):
        """ Guarantees that the repo is downloaded and on right commit. """
        if not self.ready:
            self.download()
        else:
            self.checkout()

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
        """ A branch of the repository. """
        return self.__tag

    @branch.setter
    def branch(self, new_branch):
        """ Set the repository to track a branch. """
        self.on_branch = True
        self.__tag = new_branch

    @property
    def tag(self):
        """ A tag of the repository. """
        return self.__tag

    @tag.setter
    def tag(self, new_tag):
        """ Set the repository to track a specific tag. """
        self.on_branch = False
        self.__tag = new_tag

    def clean(self):
        """ Simply purges the source tree. """
        cmd = Command('rm -rf ' + self.target)
        cmd.wait()

    @abstractproperty
    def cur_hash(self):
        """ Return the current hash of the remote repo. """
        raise NotImplementedError

    @abstractproperty
    def ready(self):
        """ Returns true iff the target exists & is correct. """
        raise NotImplementedError

    @abstractmethod
    def checkout(self):
        """ Equivalent to git checkout for vcs, updates ref. """
        raise NotImplementedError

    @abstractmethod
    def download(self):
        """ Download the repo to with specified opts.

            target: Set target directory before downloading.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """ Fetches latest changeset and updates current branch. """
        raise NotImplementedError


class Git(VersionRepo):
    """ Represents a git repository. """
    def __init__(self, uri, **kwargs):
        super(Git, self).__init__(uri, **kwargs)

    @property
    def cur_hash(self):
        """ Return the current hash of the remote repo. """
        self.get_it()
        cmd = Command('git log -1 ', self.target)
        cmd.wait()
        hash_line = cmd.output()[0]
        return hash_line.split()[-1]

    @property
    def ready(self):
        """ True iff the target exists & is the required repository. """
        if not os.path.exists(os.path.join(self.target, '.git')):
            return False

        cmd = Command('git remote show origin', self.target)
        cmd.wait()
        return self.uri in cmd.output()[1]

    def checkout(self):
        """ Updates the repository to the tag. """
        if self.tag is not None:
            cmd = Command('git checkout ' + self.tag, self.target)
            cmd.wait()

    def download(self):
        """ Download the repo to target.

            target: Where the repository will be stored
        """
        tag = '' if self.tag is None else '-b ' + self.tag
        cmd = Command('git clone --recursive {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()

        if self.on_branch and self.tag is None:
            cmd = Command('git branch', self.target)
            cmd.wait()
            lines = [line for line in cmd.output() if line.find('*') == 0]
            self.branch = lines[0][2:]

    def update(self):
        cmd = Command('git fetch origin +{0}:new{0}'.format(self.branch),
                      self.target)
        cmd.wait()
        cmd = Command('git merge --ff-only new' + self.branch, self.target)
        cmd.wait()


class Hg(VersionRepo):
    """ Represents a mercurial repository. """
    def __init__(self, uri, **kwargs):
        super(Hg, self).__init__(uri, **kwargs)

    @property
    def cur_hash(self):
        """ Return the current hash of the remote repo. """
        self.get_it()
        cmd = Command('hg parents', self.target)
        cmd.wait()
        hash_line = cmd.output()[0]
        return hash_line.split()[-1]

    @property
    def ready(self):
        """ True iff the target exists & is the required repository. """
        if not os.path.exists(os.path.join(self.target, '.hg')):
            return False

        found = False
        with open(os.path.join(self.target, '.hg', 'hgrc')) as fin:
            for line in fin:
                if self.uri in line:
                    found = True
                    break

        return found

    def checkout(self):
        """ Updates the repository to the tag. """
        if self.tag is not None:
            cmd = Command('hg update ' + self.tag, self.target)
            cmd.wait()

    def download(self):
        """ Download the repo to target.

            target: Where the repository will be stored
        """
        tag = '' if self.tag is None else '-u ' + self.tag
        cmd = Command('hg clone {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()

        if self.on_branch and self.tag is None:
            cmd = Command('hg branch', self.target)
            cmd.wait()
            self.branch = cmd.output()[0]

    def update(self):
        cmd = Command('hg pull -b ' + self.branch, self.target)
        cmd.wait()
        cmd = Command('hg update', self.target)
        cmd.wait()


# TODO: Make this unecessary
@atexit.register
def cmd_cleanup():
    """ Cleans up any command stdout files left over,
        sometimes happen due to errors during testing. """
    for filename in glob.glob(os.path.join(TMP_DIR, 'cmd*')):
        try:
            os.remove(filename)
        except OSError:
            logging.error('Could not delete file %s.', filename)
            raise


class CmdFailed(Exception):
    """ Command did not return sucessfully. """
    pass


class Command(object):
    """ Represent a command to be run on the system.
        Command is running once constructor returns.
    """
    def __init__(self, cmd, cmd_dir=None):
        super(Command, self).__init__()
        if isinstance(cmd, list):
            self._cmd = cmd
        else:
            self._cmd = shlex.split(cmd)
        self._cmd_dir = cmd_dir
        self._stdout = NamedTemporaryFile(mode='wb', delete=True,
                                          dir=TMP_DIR, prefix='cmd',
                                          suffix='.log')
        logging.debug('CMD START: %s', self)
        self._proc = sub.Popen(
            self._cmd, cwd=self._cmd_dir,
            stdout=self._stdout, stderr=sub.STDOUT,
            preexec_fn=os.setsid
        )

    def __del__(self):
        """ Ensure terminated & fully logged for tracking. """
        try:
            if self.alive:
                self.terminate()
            prefix = '\n    '
            msg = prefix + prefix.join(self.output())
            logging.debug("CMD LOG: %s%s", self, msg)
            self._stdout.close()
        except (AttributeError, IOError) as exc:
            logging.error(exc)
            raise

    def __str__(self):
        return 'Command: {0}, {1}'.format(self._cmd, self._cmd_dir)

    @property
    def alive(self):
        """ Returns if the process is running. """
        return self._proc.poll() is None

    @property
    def rcode(self):
        """ Returns the return code. """
        return self._proc.returncode

    def output(self, last_n=0):
        """ Return by default all stdout from command.

            last_n: Return last n lines from output.
        """
        if self._proc is None:
            return []

        with open(self._stdout.name, 'r') as out:
            lines = [line.rstrip() for line in out.readlines()]

        return lines[-last_n:]

    def terminate(self):
        """ Terminate the process and all children.
            On return, they are all dead.
        """
        os.killpg(self._proc.pid, signal.SIGTERM)
        self._proc.wait()

    def wait(self):
        """ Simple wrapper for wait, blocks until finished. """
        self._proc.wait()
        if self.rcode != 0:
            raise CmdFailed('\n'.join(self.output(10)))

# Placed here on purpose, pick up any extract funcs before me
EXTS = [func.replace('extract_', '').replace('_', '.') for func
        in dir(sys.modules[__name__]) if func.find('extract_') == 0]
