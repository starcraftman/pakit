""" All things shell related, including Command class. """
from __future__ import absolute_import

import atexit
import glob
import logging
import os
import shlex
import signal
import subprocess as sub
import tempfile

TMP_DIR = '/tmp/wok'

class Git(object):
    """ Represent a git repository. """
    def __init__(self, src, target='', tag=None):
        self.src = src
        self.__target = target
        self.__tag = tag

    #def __enter__(self):
        #if not self.is_cloned:
            #self.download()

    #def __exit__(self, type, value, traceback):
        #self.clean()

    @property
    def is_cloned(self):
        """ True iff the target exists & is the required repository. """
        if not os.path.exists(os.path.join(self.target, '.git')):
            return False

        cmd = Command('git remote show origin', self.target)
        cmd.wait()
        if self.src not in cmd.output()[1]:
            return False

        return True

    @property
    def tag(self):
        """ A tag or branch of the git repository. """
        return self.__tag

    @tag.setter
    def tag(self, new_tag):
        self.__tag = new_tag

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, new_target):
        if os.path.exists(os.path.dirname(new_target)):
            raise IOError('Target already exists.')

        self.__target = new_target

    @property
    def version(self):
        """ Get the commit hash of the relevant repo. """
        if not self.is_cloned:
            self.download()

        cmd = Command('git log -1 ', self.target)
        cmd.wait()
        return cmd.output()[0]

    def checkout(self):
        cmd = Command('git checkout ' + self.tag, self.target)
        cmd.wait()

    def clean(self):
        cmd = Command('rm -rf ' + self.target)
        cmd.wait()

    def download(self, target=None):
        """ Download the repo to with specified opts.

            target: Change the clone target directory.
        """
        if target is not None:
            self.target = target
        if self.tag is None:
            tag = ''
        else:
            tag = '-b ' + self.tag

        cmd = Command('git clone --recursive --depth 1 {tag} {url} {target}'.format(
                tag=tag, url=self.src, target=self.target))
        cmd.wait()

def get_hg(**kwargs):
    """ Clones a mercurial repo to a target, optionally checks out a branch. """
    def_branch = {'branch': '-b ' + kwargs.get('branch')
            if kwargs.has_key('branch') else ''}
    kwargs.update(def_branch)

    cmd = Command('hg clone {url} {target}'.format(**kwargs))
    cmd.wait()

def get_git(**kwargs):
    """ Clones a git repo to a target, optionally checks out a branch. """
    def_branch = {'branch': '-b ' + kwargs.get('branch')
            if kwargs.has_key('branch') else ''}
    kwargs.update(def_branch)

    cmd = Command('git clone --recursive --depth 1 {branch} {url} {target}'.format(**kwargs))
    cmd.wait()

def get_svn(**kwargs):
    cmd = Command('svn checkout {url} {target}'.format(**kwargs))
    cmd.wait()

@atexit.register
def cmd_cleanup():
    for filename in glob.glob(os.path.join(TMP_DIR, 'cmd*')):
        try:
            os.remove(filename)
        except OSError:
            logging.error('Could not delete file %s.', filename)

class CmdFailed(Exception):
    """ Command did not return sucessfully. """
    pass

class Command(object):
    """ Represent a command to be run on the system.
        Command is running once constructor returns.
    """
    def __init__(self, cmd, cmd_dir=None):
        super(Command, self).__init__()
        self._cmd = cmd
        self._cmd_dir = cmd_dir
        self._stdout = tempfile.NamedTemporaryFile(mode='w+b',
                delete=True, dir=TMP_DIR, prefix='cmd')
        logging.debug('CMD EXEC: {0}'.format(self))
        self._proc = sub.Popen(
                shlex.split(self._cmd), cwd=self._cmd_dir,
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
        except (AttributeError, IOError):
            pass

    def __repr__(self):
        return '{0}'.format(self._cmd)

    def __str__(self):
        return '{0} -> {1}'.format(self._cmd_dir, self._cmd)

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

