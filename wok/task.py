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
        link_dst = dirpath.replace(src, dst)
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
                logging.error('Could not symlink {0} -> {1}'.format(
                    sfile, dfile))

def walk_and_unlink(src, dst):
    """ Before removing program, take care of links. """
    for dirpath, _, filenames in os.walk(src,
            topdown=False, followlinks=True):
        link_dst = dirpath.replace(src, dst)
        for fname in filenames:
            os.remove(os.path.join(link_dst, fname))

        try:
            os.rmdir(link_dst)
        except OSError:
            pass

class Task(object):
    """ Represents a task for a recipe. """
    __metaclass__ = ABCMeta
    __config = None

    def __init__(self, recipe_name=None):
        super(Task, self).__init__()
        if recipe_name is not None:
            self.__recipe = RecipeDB().get(recipe_name)

    def __str__(self):
        return '{cls}: {recipe}'.format(cls=self.__class__.__name__,
                recipe=self.recipe)

    @classmethod
    def config(cls):
        return cls.__config

    @classmethod
    def set_config(cls, new_config):
        cls.__config = new_config

    def __path(self, name):
        return self.__class__.__config.get('paths.' + name)

    @property
    def link(self):
        return self.__path('link')

    @property
    def prefix(self):
        return self.__path('prefix')

    @property
    def source(self):
        return self.__path('source')

    @property
    def recipe(self):
        return self.__recipe

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
        logging.debug('Installing %s', self.recipe)
        with self.recipe.unstable:
            self.recipe.build()
            walk_and_link(self.recipe.install_dir(), self.recipe.link_dir())
            sucess = self.recipe.verify()
        return sucess

class RemoveTask(Task):
    def __init__(self, recipe_name):
        super(RemoveTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Removing %s', self.recipe)
        walk_and_unlink(self.recipe.install_dir(), self.recipe.link_dir())
        shutil.rmtree(self.recipe.install_dir())

class UpdateTask(Task):
    """ Update a program, don't do it unless changes made. """
    def __init__(self, recipe_name):
        super(UpdateTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Updating %s', self.recipe)

class ListInstalled(Task):
    """ List all installed programs. """
    def __init__(self):
        super(ListInstalled, self).__init__()

    def installed(self):
        """ Returns all recipes currently installed. """
        return [RecipeDB().get(prog) for prog in os.listdir(self.prefix)]

    def do(self):
        logging.debug('List Task')
        msg = 'The following programs are installed:'
        msg += ''.join(['\n-  ' + str(prog) for prog in self.installed()])
        print msg
        return msg
