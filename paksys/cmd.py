"""
Everything to do with running commands on the system.
"""
from __future__ import absolute_import
import atexit
import logging
import os
import shlex
import shutil
import signal
import subprocess
import threading
import time
from tempfile import NamedTemporaryFile as TempFile

import pakit.conf
from pakit.exc import PakitCmdError, PakitCmdTimeout


@atexit.register
def cmd_cleanup():
    """
    Cleans up any command stdout files left over,
    """
    shutil.rmtree(pakit.conf.TMP_DIR)


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
