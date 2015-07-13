""" All logic to manage the installation of a program. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import logging
import os

from wok.recipe import RecipeDB

def walk_and_link(src, dst):
    """ After installing, link a program to dst. """
    for dirpath, _, filenames in os.walk(src, followlinks=True):
        link_dst = os.path.join(dst, dirpath.replace(src + '/', ''))
        try:
            os.makedirs(link_dst)
        except OSError:
            pass

        for fname in filenames:
            try:
                sfile = os.path.join(dirpath, fname)
                dfile = os.path.join(link_dst, fname)
                os.symlink(sfile, dfile)
            except OSError:
                logging.error('Could not symlink {0} -> {1}'.format(sfile,
                        dfile))

def walk_and_unlink(src, dst):
    """ Before removing program, take care of links. """
    for dirpath, _, filenames in os.walk(src,
            topdown=False, followlinks=True):
        link_dst = os.path.join(dst, dirpath.replace(src + '/', ''))
        for fname in filenames:
            os.remove(os.path.join(link_dst, fname))

        try:
            os.rmdir(link_dst)
        except OSError:
            pass

class Task(object):
    """ Top level task. """
    __metaclass__ = ABCMeta

    def __init__(self, config, recipe_name=None):
        self.__config = config

    @property
    def link(self):
        return self.__config.paths.get('link')

    @property
    def prefix(self):
        return self.__config.paths.get('prefix')

    @property
    def source(self):
        return self.__config.paths.get('source')

    @abstractmethod
    def do(self):
        pass

class InstallTask(Task):
    def __init__(self, config, recipe_name):
        super(InstallTask, self).__init__(config)
        self.recipe_name = recipe_name

    def do(self):
        self.install()

    def install(self):
        logging.debug('Installing %s', self.recipe_name)
        recipe = RecipeDB().get(self.recipe_name)
        with recipe.unstable:
            recipe.build()
            walk_and_link(recipe.install_dir(), recipe.link_dir())
            sucess = recipe.verify()
        return sucess

class ListTask(Task):
    """ List all installed programs. """
    def __init__(self, config):
        super(ListTask, self).__init__(config)

    def do(self):
        logging.debug('List Action')
        installed = os.listdir(self.prefix)
        msg = 'The following programs are installed:\n'
        for prog in installed:
            msg += '* ' + prog

        return msg
