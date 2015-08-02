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
import tempfile

TMP_DIR = '/tmp/wok'


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
            self.__on_branch = False
        else:
            self.__tag = kwargs.get('branch', None)
            self.__on_branch = True

    def __enter__(self):
        """ Guarantees that the repo is downloaded then cleaned. """
        if not self.is_cloned:
            self.download()

    def __exit__(self, typ, value, traceback):
        self.clean()

    def __str__(self):
        if self.__on_branch:
            tag = 'default' if self.tag is None else self.tag
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
        self.__on_branch = True
        self.__tag = new_branch

    @property
    def tag(self):
        """ A tag of the repository. """
        return self.__tag

    @tag.setter
    def tag(self, new_tag):
        self.__on_branch = False
        self.__tag = new_tag

    @property
    def target(self):
        """ Path to clone the repository to. """
        return self.__target

    @target.setter
    def target(self, new_target):
        if os.path.exists(new_target):
            msg = 'Target Already Exists: ' + new_target
            logging.error(msg)
            raise IOError(msg)
        self.__target = new_target

    def clean(self):
        """ Simply purges the source tree. """
        cmd = Command('rm -rf ' + self.target)
        cmd.wait()

    @abstractproperty
    def repo_hash(self):
        """ Return the current hash of the remote repo. """
        pass

    @abstractproperty
    def is_cloned(self):
        """ Returns true iff the target exists & is correct. """
        pass

    @abstractmethod
    def checkout(self):
        """ Equivalent to git checkout for vcs, updates ref. """
        pass

    @abstractmethod
    def download(self, target=None):
        """ Download the repo to with specified opts.

            target: Set target directory before downloading.
        """
        pass


class Git(VersionRepo):
    """ Represents a git repository. """
    def __init__(self, uri, **kwargs):
        super(Git, self).__init__(uri, **kwargs)

    @property
    def repo_hash(self):
        """ Return the current hash of the remote repo. """
        def __cmd():
            cmd = Command('git log -1 ', self.target)
            cmd.wait()
            return cmd.output()[0]

        if not self.is_cloned:
            with self:
                repo_hash = __cmd()
        else:
            repo_hash = __cmd()

        return repo_hash.split()[-1]

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
        cmd = Command('git checkout ' + self.tag, self.target)
        cmd.wait()

    def download(self, target=None):
        """ Download the repo to target.

            target: Where the repository will be stored
        """
        if target is not None:
            self.target = target
        tag = '' if self.tag is None else '-b ' + self.tag

        cmd = Command('git clone --recursive {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()


class Hg(VersionRepo):
    """ Represents a mercurial repository. """
    def __init__(self, uri, **kwargs):
        super(Hg, self).__init__(uri, **kwargs)

    @property
    def repo_hash(self):
        """ Return the current hash of the remote repo. """
        def __cmd():
            cmd = Command('hg parents', self.target)
            cmd.wait()
            return cmd.output()[0]

        if not self.is_cloned:
            with self:
                repo_hash = __cmd()
        else:
            repo_hash = __cmd()

        return repo_hash.split()[-1]

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
        cmd = Command('hg update ' + self.tag, self.target)
        cmd.wait()

    def download(self, target=None):
        """ Download the repo to target.

            target: Where the repository will be stored
        """
        if target is not None:
            self.target = target
        tag = '' if self.tag is None else '-u ' + self.tag

        cmd = Command('hg clone {tag} {uri} {target}'.format(
            tag=tag, uri=self.uri, target=self.target))
        cmd.wait()


@atexit.register
def cmd_cleanup():
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
        self._stdout = tempfile.NamedTemporaryFile(mode='w+b',
                                                   delete=True,
                                                   dir=TMP_DIR,
                                                   prefix='cmd')
        logging.debug('CMD START: {0}'.format(self))
        self._proc = sub.Popen(
            self._cmd, cwd=self._cmd_dir,
            stdout=self._stdout, stderr=sub.STDOUT,
            preexec_fn=os.setsid
        )

    def __del__(self):
        """ Ensure terminated & fully logged for tracking. """
        try:
            prefix = '\n    '
            msg = prefix[1:] + prefix.join(self.output())
            logging.debug("CMD LOG: %s\n%s", self, msg)
            if self.alive:
                self.terminate()
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
