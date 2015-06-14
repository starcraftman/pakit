""" All things shell related, including Command class. """
from __future__ import absolute_import

import logging
import os
import shlex
import signal
import subprocess as sub
import tempfile

LOGFILE = os.path.expanduser('/tmp/wok/commands.log')
os.makedirs(os.path.dirname(LOGFILE))
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)

class Command(object):
    """ Represent a command to be run on the system. """
    def __init__(self, cmd, cmd_dir=None):
        super(Command, self).__init__()
        self._cmd = shlex.split(cmd)
        self._cmd_dir = cmd_dir
        self._proc = None
        self._stdout = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
        self._stderr = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
        logging.debug("CMD NEW: %s", self._cmd)

    def __del__(self):
        """ Clean up at end. """
        try:
            if self._proc is not None:
                self.terminate()
            self._stdout.close()
            self._stderr.close()
        except (ValueError, OSError):
            pass
        logging.debug("CMD DEL: %s", self._cmd)

    @property
    def pid(self):
        """ Returns the PID of the spawned process. """
        return self._proc.pid

    @property
    def rcode(self):
        """ Returns the return code, if not finished returns None """
        return self._proc.returncode

    @property
    def alive(self):
        """ Returns if the process is running. """
        return self._proc.poll() == None

    @property
    def proc(self):
        """ Provides direct access, will be removed later. """
        return self._proc

    def execute(self):
        """ Execute the given command. """
        self._proc = sub.Popen(
                self._cmd, cwd=self._cmd_dir,
                stdout=self._stdout, stderr=sub.STDOUT,
                preexec_fn=os.setsid
        )
        logging.debug("CMD EXECUTING: %s", self._cmd)

    def wait(self):
        """ Simple wrapper for wait, blocks until finished. """
        self._proc.wait()

    def output(self):
        """ Return stdout from command. """
        with open(self._stdout.name, 'r') as out:
            lines = [line.rstrip() for line in out.readlines()]
            logging.debug(str(lines))
            return lines

    def terminate(self):
        """ Terminate the process and all children.
            On return, they are all dead.
        """
        os.killpg(self.pid, signal.SIGTERM)
        self.proc.wait()
