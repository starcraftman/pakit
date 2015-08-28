""" All logic to manage the installation of a program. """
from __future__ import absolute_import, print_function
from abc import ABCMeta, abstractmethod

import logging
import os
import shutil

from pakit.exc import PakitError, PakitCmdError, PakitLinkError
from pakit.recipe import Recipe, RecipeDB
from pakit.shell import Command

IDB = None
PREFIX = '\n  '


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
                msg = 'Could not symlink {0} -> {1}'.format(sfile, dfile)
                logging.error(msg)
                raise PakitLinkError(msg)


def walk_and_unlink(src, dst):
    """ Before removing program, take care of links. """
    for dirpath, _, filenames in os.walk(src, topdown=False, followlinks=True):
        link_dst = dirpath.replace(src, dst)
        for fname in filenames:
            try:
                os.remove(os.path.join(link_dst, fname))
            except OSError:
                pass  # link was not there

        try:
            os.rmdir(link_dst)
        except OSError:  # pragma: no cover
            pass


class Task(object):
    """ Universal task interface. """
    __metaclass__ = ABCMeta
    config = None

    def __str__(self):
        return '{cls}: Config File {config}'.format(
            cls=self.__class__.__name__,
            config=Task.config.filename)

    @classmethod
    def set_config(cls, new_config):
        """ Set the global config for all tasks. """
        cls.config = new_config

    def path(self, name):
        """ Returns the name from the config `paths` dict. """
        return self.__class__.config.get('paths.' + name)

    @abstractmethod
    def run(self):
        """ A unversal interface to do an arbitrary action. """
        raise NotImplementedError


class RecipeTask(Task):
    """ Represents a task for a recipe. """
    def __init__(self, recipe):
        super(RecipeTask, self).__init__()
        if isinstance(recipe, Recipe):
            self.__recipe = recipe
        else:
            self.__recipe = RecipeDB().get(recipe)

    def __str__(self):
        return '{cls}: {recipe}'.format(cls=self.__class__.__name__,
                                        recipe=self.recipe)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.recipe.name != other.recipe.name:
            return False

        return True

    @property
    def recipe(self):
        """ Access the underlying recipe directly. """
        return self.__recipe

    def run(self):
        raise NotImplementedError


class InstallTask(RecipeTask):
    """ Install a recipe. """
    def __init__(self, recipe):
        super(InstallTask, self).__init__(recipe)

    def rollback(self, exc):
        """ Based on type of exception, rollback state. """
        cascade = False
        if isinstance(exc, AssertionError):
            logging.error('Error during verify() of %s', self.recipe.name)
            cascade = True
        if isinstance(exc, PakitLinkError) or cascade:
            if not cascade:
                logging.error('Error during linking of %s', self.recipe.name)
            walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
            cascade = True
        if isinstance(exc, PakitCmdError) or cascade:
            if not cascade:
                logging.error('Error during build() of %s', self.recipe.name)
            if os.path.exists(self.recipe.repo.target):
                prefix = os.path.join(self.path('prefix'), self.recipe.name)
                Command('rm -rf ' + prefix).wait()
        # In all cases, purge src tree for safety
        self.recipe.repo.clean()

    def run(self):
        logging.debug('Installing: %s', self.recipe.name)

        entry = IDB.get(self.recipe.name)
        if entry is not None:
            logging.error('\nInstalled: %s\n  Built On: %s\n  Hash: %s',
                          self.recipe.name, entry['date'], entry['hash'])
            return

        try:
            self.recipe.repo.get_it()
            self.recipe.build()
            walk_and_link(self.recipe.install_dir, self.recipe.link_dir)
            self.recipe.verify()
            IDB.add(self.recipe)
            self.recipe.repo.clean()
        except (AssertionError, PakitError) as exc:
            self.rollback(exc)
            raise


class RemoveTask(RecipeTask):
    """ Remove a recipe. """
    def __init__(self, recipe):
        super(RemoveTask, self).__init__(recipe)

    def run(self):
        logging.debug('Removing: %s', self.recipe.name)

        if IDB.get(self.recipe.name) is None:
            logging.error('Not Installed: ' + self.recipe.name)
            return

        walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
        shutil.rmtree(self.recipe.install_dir)
        IDB.remove(self.recipe.name)


class UpdateTask(RecipeTask):
    """ Update a program, don't do it unless changes made. """
    def __init__(self, recipe):
        super(UpdateTask, self).__init__(recipe)
        self.back_dir = self.recipe.install_dir + '_bak'
        self.old_entry = None

    def save_old_install(self):
        """ Before updating, unlink and save old version. """
        walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
        self.old_entry = IDB.get(self.recipe.name)
        IDB.remove(self.recipe.name)
        shutil.move(self.recipe.install_dir, self.back_dir)

    def restore_old_install(self):
        """ Update failed, restore old version. """
        shutil.move(self.back_dir, self.recipe.install_dir)
        IDB.set(self.recipe.name, self.old_entry)
        walk_and_link(self.recipe.install_dir, self.recipe.link_dir)

    def run(self):
        logging.debug('Updating: %s', self.recipe.name)

        if IDB.get(self.recipe.name)['hash'] == self.recipe.repo.cur_hash:
            return

        try:
            self.save_old_install()
            InstallTask(self.recipe).run()
            Command('rm -rf ' + self.back_dir).wait()
        except (AssertionError, PakitError):
            self.restore_old_install()


class DisplayTask(RecipeTask):
    """ Display detailed recipe information. """
    def __init__(self, recipe):
        super(DisplayTask, self).__init__(recipe)

    def run(self):
        logging.debug('Displaying Info: ' + self.recipe.name)

        msg = self.recipe.info()
        print(msg)
        return msg


class ListInstalled(Task):
    """ List all installed programs. """
    def __init__(self):
        super(ListInstalled, self).__init__()

    def run(self):
        logging.debug('List Installed Programs')
        fmt = '{prog:10}   {date}   {hash}'
        installed = ['Program      Date                Hash or Version']
        installed.extend([fmt.format(prog=prog, **entry)
                          for prog, entry in IDB])

        msg = 'Installed Programs:'
        msg += PREFIX + PREFIX.join(installed)
        print(msg)
        return msg


class ListAvailable(Task):
    """ List all available recipes. """
    def __init__(self):
        super(ListAvailable, self).__init__()

    def run(self):
        logging.debug('List Available Recipes')
        available = ['Program      Description']
        available.extend(RecipeDB().names(desc=True))

        msg = 'Available Recipes:'
        msg += PREFIX + PREFIX.join(available)
        print(msg)
        return msg


def subseq_match(word, sequence):
    """ Subsequence matcher, not case senstive. """
    seq = list(sequence.lower())
    for char in word.lower():
        if char == seq[0]:
            seq.remove(seq[0])
        if len(seq) == 0:
            return True
    return False


def substring_match(word, sequence):
    """ Substring matcher, matches exact substring sequence. """
    return word.lower().find(sequence.lower()) != -1


class SearchTask(Task):
    """ Search logic, returns list matching sequence. """
    def __init__(self, words, queries):
        super(SearchTask, self).__init__()
        self.queries = queries
        self.words = words

    def run(self):
        matched = []
        for query in self.queries:
            match_query = [word for word in self.words
                           if substring_match(word, query)]
            matched.extend(match_query)
        matched = ['Program      Description'] + sorted(list(set(matched)))

        msg = 'Your Search For:'
        msg += PREFIX + PREFIX.join(["'{0}'".format(q) for q in self.queries])
        msg += '\nMatched These Recipes:'
        msg += PREFIX + PREFIX.join(matched)
        print(msg)
        return matched
