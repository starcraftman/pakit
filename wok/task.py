""" All logic to manage the installation of a program. """
from __future__ import absolute_import, print_function
from abc import ABCMeta, abstractmethod

import logging
import os
import shutil

from wok.recipe import RecipeDB

IDB = None


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
    for dirpath, _, filenames in os.walk(src, topdown=False, followlinks=True):
        link_dst = dirpath.replace(src, dst)
        for fname in filenames:
            os.remove(os.path.join(link_dst, fname))

        try:
            os.rmdir(link_dst)
        except OSError:
            pass


class Task(object):
    """ Universal task interface. """
    __metaclass__ = ABCMeta
    __config = None

    def __str__(self):
        return '{cls}:\n{config}'.format(cls=self.__class__.__name__,
                                         config=str(Task.__config))

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

    @abstractmethod
    def do(self):
        pass


class RecipeTask(Task):
    """ Represents a task for a recipe. """
    def __init__(self, recipe_name):
        super(RecipeTask, self).__init__()
        self.__recipe = RecipeDB().get(recipe_name)

    def __str__(self):
        return '{cls}: {recipe}'.format(cls=self.__class__.__name__,
                                        recipe=self.recipe)

    @property
    def recipe(self):
        return self.__recipe


class InstallTask(RecipeTask):
    """ Install a recipe. """
    def __init__(self, recipe_name):
        super(InstallTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Installing: %s', self.recipe.name)

        if IDB.get(self.recipe.name) is not None:
            logging.error('Already Installed: ' + self.recipe.name)
            return

        with self.recipe.unstable:
            self.recipe.build()
            walk_and_link(self.recipe.install_dir, self.recipe.link_dir)
            self.recipe.verify()
            IDB.add(self.recipe.name, self.recipe.unstable.cur_hash)


class RemoveTask(RecipeTask):
    """ Remove a recipe. """
    def __init__(self, recipe_name):
        super(RemoveTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Removing: %s', self.recipe.name)

        if IDB.get(self.recipe.name) is None:
            logging.error('Not Installed: ' + self.recipe.name)
            return

        walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
        shutil.rmtree(self.recipe.install_dir)
        IDB.remove(self.recipe.name)


class UpdateTask(RecipeTask):
    """ Update a program, don't do it unless changes made. """
    def __init__(self, recipe_name):
        super(UpdateTask, self).__init__(recipe_name)

    def do(self):
        logging.debug('Updating: %s', self.recipe.name)

        if IDB.get(self.recipe.name)['hash'] == self.recipe.unstable.cur_hash:
            return
        RemoveTask(self.recipe.name).do()
        InstallTask(self.recipe.name).do()


class ListInstalled(Task):
    """ List all installed programs. """
    def __init__(self):
        super(ListInstalled, self).__init__()

    def do(self):
        logging.debug('List Task')

        longest = ''
        for prog, _ in IDB:
            if len(prog) > longest:
                longest = prog
        longest = str(len(longest) + 1)

        fmt = '{prog:' + longest + '} | {date} | {hash}'
        installed = [fmt.format(prog=prog, **entry) for prog, entry in IDB]
        msg = 'Installed:'
        msg += '\nProgram | Date | Hash or Version'
        msg += ''.join(['\n-  ' + prog for prog in installed])
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
    def __init__(self, sequence, words):
        super(SearchTask, self).__init__()
        self.sequence = sequence
        self.words = words

    def do(self):
        matched = []
        for word in self.words:
            if substring_match(word, self.sequence):
                matched.append(word)

        print('\n'.join(matched))
        return matched
