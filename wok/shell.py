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

def get_hg(**kwargs):
    """ Clones a mercurial repo to a target, optionally checks out a branch. """
    def_branch = {'branch': '-b ' + kwargs.get('branch')
            if kwargs.has_key('branch') else ''}
    kwargs.update(def_branch)

    cmd = Command('hg clone {url} {target}'.format(**kwargs))
    cmd.execute()
    cmd.wait()

def get_git(**kwargs):
    """ Clones a git repo to a target, optionally checks out a branch. """
    def_branch = {'branch': '-b ' + kwargs.get('branch')
            if kwargs.has_key('branch') else ''}
    kwargs.update(def_branch)

    cmd = Command('git clone --recursive --depth 1 {branch} {url} {target}'.format(**kwargs))
    cmd.execute()
    cmd.wait()

def get_svn(**kwargs):
    cmd = Command('svn checkout {url} {target}'.format(**kwargs))
    cmd.execute()
    cmd.wait()

@atexit.register
def cmd_cleanup():
    for filename in glob.glob(os.path.join(TMP_DIR, 'cmd*')):
        try:
            os.remove(filename)
        except OSError:
            logging.error('Could not delete file %s.', filename)

class Command(object):
    """ Represent a command to be run on the system. """
    def __init__(self, cmd, cmd_dir=None):
        super(Command, self).__init__()
        self._cmd = cmd
        self._cmd_dir = cmd_dir
        self._proc = None
        self._stdout = tempfile.NamedTemporaryFile(mode='w+b',
                delete=True, dir=TMP_DIR, prefix='cmd')

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
    def proc(self):
        """ Provides direct access, will be removed later. """
        return self._proc

    @property
    def rcode(self):
        """ Returns the return code. """
        return self._proc.returncode

    def execute(self):
        """ Execute the given command. """
        logging.debug('CMD EXEC: {0}'.format(self))
        self._proc = sub.Popen(
                shlex.split(self._cmd), cwd=self._cmd_dir,
                stdout=self._stdout, stderr=sub.STDOUT,
                preexec_fn=os.setsid
        )

    def wait(self):
        """ Simple wrapper for wait, blocks until finished. """
        self._proc.wait()

    def output(self):
        """ Return stdout from command. """
        if self._proc is None:
            return []

        with open(self._stdout.name, 'r') as out:
            lines = [line.rstrip() for line in out.readlines()]
            return lines

    def terminate(self):
        """ Terminate the process and all children.
            On return, they are all dead.
        """
        os.killpg(self._proc.pid, signal.SIGTERM)
        self.proc.wait()
