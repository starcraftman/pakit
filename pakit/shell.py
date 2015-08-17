""" All things shell related, including Command class. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod, abstractproperty

import atexit
import glob
import logging
import os
import shlex
import signal
import subprocess as sub
from tempfile import NamedTemporaryFile

TMP_DIR = '/tmp/pakit'


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
        self.__target = kwargs.get('target', None)
        tag = kwargs.get('tag', None)
        if tag is not None:
            self.__tag = tag
            self.on_branch = False
        else:
            self.__tag = kwargs.get('branch', None)
            self.on_branch = True

    def make_available(self):
        """ Guarantees that the repo is downloaded and on right commit. """
        if not self.is_cloned:
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

    @property
    def target(self):
        """ Path to clone the repository to. """
        return self.__target

    @target.setter
    def target(self, new_target):
        """ Set the path to clone to. """
        self.__target = new_target

    def clean(self):
        """ Simply purges the source tree. """
        cmd = Command('rm -rf ' + self.target)
        cmd.wait()

    @abstractproperty
    def cur_hash(self):
        """ Return the current hash of the remote repo. """
        raise NotImplementedError

    @abstractproperty
    def is_cloned(self):
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
        self.make_available()
        cmd = Command('git log -1 ', self.target)
        cmd.wait()
        hash_line = cmd.output()[0]
        return hash_line.split()[-1]

    @property
    def is_cloned(self):
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
        self.make_available()
        cmd = Command('hg parents', self.target)
        cmd.wait()
        hash_line = cmd.output()[0]
        return hash_line.split()[-1]

    @property
    def is_cloned(self):
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
        self._stdout = NamedTemporaryFile(mode='w+b', delete=True,
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
