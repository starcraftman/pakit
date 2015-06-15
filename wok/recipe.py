""" The base class for build recipes. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import os

from wok.shell import Command

class Recipe(object):
    """ A schema to build some binary. """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self._desc = 'Short description for the recipe.'
        self._src = 'Source code url, will build bleeding edge version.'
        self._homepage = 'Project site'
        self._idir = None

    def sdir(self):
        return os.path.join(self._idir, 'src')

    def idir(self):
        return self._idir

    def set_idir(self, idir):
        self._idir = idir

    def cmd(self, cmd_str, cmd_dir=None):
        cmd = Command(cmd_str, cmd_dir)
        cmd.execute()
        cmd.wait()

        return cmd.output()

    def download(self):
        """ Git source checkout. """
        cmd = Command('git clone --recursive --depth 1 {0} {1}'.format(
                self._src, self.sdir()))
        cmd.execute()
        cmd.wait()

    @abstractmethod
    def build(self):
        """ Build the program. """
        pass

    @abstractmethod
    def verify(self):
        """ Verify it works somehow. """
        pass
