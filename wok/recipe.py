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
        self.desc = 'Short description for the recipe.'
        self.url_src = 'Source code url, will build bleeding edge version.'
        self.homepage = 'Project site'
        self.install_d = 'Where final install should be rooted'

    def source_dir(self):
        return os.path.join(self.install_d, 'src')

    def install_dir(self):
        return self.install_d

    def cmd(self, cmd_str, in_build=True):
        if in_build is True:
            cmd_dir = self.source_dir()
        elif in_build is False:
            cmd_dir = self.install_dir()
        else:
            cmd_dir = in_build

        cmd_str = cmd_str.format(prefix=self.install_dir())
        cmd = Command(cmd_str, cmd_dir)
        cmd.execute()
        cmd.wait()

        return cmd.output()

    def download(self):
        """ Git source checkout. """
        cmd = Command('git clone --recursive --depth 1 {0} {1}'.format(
                self.url_src, self.source_dir()))
        cmd.execute()
        cmd.wait()

    def clean(self):
        """ Cleanup, by default delete src dir. """
        self.cmd('rm -rf {0}'.format(self.source_dir()))

    @abstractmethod
    def build(self):
        """ Build the program. """
        pass

    @abstractmethod
    def verify(self):
        """ Verify it works somehow. """
        pass
