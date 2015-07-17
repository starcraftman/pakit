""" All logic to manage the installation of a program. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import logging
import os
import shutil

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
    __config = None

    def __init__(self, recipe_name=None):
        self.__recipe_name = recipe_name

    def __str__(self):
        return '{cls}: {recipe}'.format(cls=self.__class__.__name__, recipe=self.recipe_name)

    @classmethod
    def config(cls):
        return cls.__config

    @classmethod
    def set_config(cls, new_config):
        cls.__config = new_config

    @property
    def link(self):
        return self.__class__.__config.paths.get('link')

    @property
    def prefix(self):
        return self.__class__.__config.paths.get('prefix')

    @property
    def source(self):
        return self.__class__.__config.paths.get('source')

    @property
    def recipe_name(self):
        return self.__recipe_name

    @abstractmethod
    def do(self):
        pass

class InstallTask(Task):
    def __init__(self, recipe_name):
        super(InstallTask, self).__init__(recipe_name)

    def do(self):
        self.install()

    def install(self):
        """ Separate function to subclass for update task. """
        logging.debug('Installing %s', self.recipe_name)
        recipe = RecipeDB().get(self.recipe_name)
        with recipe.unstable:
            recipe.build()
            walk_and_link(recipe.install_dir(), recipe.link_dir())
            sucess = recipe.verify()
        return sucess

class RemoveTask(Task):
    def __init__(self, recipe_name):
        super(RemoveTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Removing %s', self.recipe_name)
        recipe = RecipeDB().get(self.recipe_name)

        walk_and_unlink(recipe.install_dir(), recipe.link_dir())
        shutil.rmtree(recipe.install_dir())

class UpdateTask(Task):
    """ Update a program, don't do it unless changes made. """
    def __init__(self, recipe_name):
        super(UpdateTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Updating %s', self.recipe_name)

class ListTask(Task):
    """ List all installed programs. """
    def __init__(self):
        super(ListTask, self).__init__()

    def do(self):
        logging.debug('List Action')
        installed = os.listdir(self.prefix)
        msg = 'The following programs are installed:\n'
        for prog in installed:
            msg += '* ' + prog

        print msg

        return msg
