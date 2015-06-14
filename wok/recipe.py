""" The base class for build recipes. """
from __future__ import absolute_import
from wok.shell import Command

class Recipe(object):
    """ A schema to build some binary. """
    def __init__(self):
        pass

    def cmd(self, cmd_str):
        pass
