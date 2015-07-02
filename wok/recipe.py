""" The base class for build recipes. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import os

from wok.shell import Command, get_git

class Recipe(object):
    """ A schema to build some binary. """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self.desc = 'Short description for the recipe.'
        self.src = 'Source code url, will build bleeding edge version.'
        self.homepage = 'Project site'
        self.paths = None

    def set_paths(self, paths):
        self.paths = paths

    def install_dir(self):
        return os.path.join(self.paths.get('prefix'), self.name())

    def link_dir(self):
        return self.paths.get('link')

    def source_dir(self):
        return os.path.join(self.paths.get('source'), self.name())

    def name(self):
        return self.__class__.__name__.lower()

    def cmd(self, cmd_str, cmd_dir=None):
        # FIXME: Temporary hack, need to refactor cmd function.
        if cmd_dir is None:
            if os.path.exists(self.source_dir()):
                cmd_dir = self.source_dir()
            else:
                cmd_dir = os.path.dirname(self.link_dir())

        # TODO: Later, pickup opts from config & extend with prefix.
        opts = {'link': self.link_dir(), 'prefix': self.install_dir(),
                'source': self.source_dir()}
        cmd_str = cmd_str.format(**opts)
        cmd = Command(cmd_str, cmd_dir)
        cmd.execute()
        cmd.wait()

        return cmd.output()

    def download(self):
        """ Git source checkout. """
        get_git(url=self.src, target=self.source_dir())

    def clean(self):
        """ Cleanup, by default delete src dir. """
        self.cmd('rm -rf {source}')

    @abstractmethod
    def build(self):
        """ Build the program. """
        pass

    @abstractmethod
    def verify(self):
        """ Verify it works somehow. """
        pass
