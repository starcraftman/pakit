"""
The Tasks that pakit can perform for the user.

Any action is implemented as a Task that implements a simple
'run' command to be called. At the moment all tasks are executed
in the order they are taken from the command line.
"""
from __future__ import absolute_import, print_function
from abc import ABCMeta, abstractmethod

import logging
import shutil

import pakit.conf
from pakit.exc import PakitCmdError, PakitLinkError
from pakit.recipe import Recipe, RecipeDB
from pakit.shell import Command, walk_and_link, walk_and_unlink

PREFIX = '\n  '
USER = logging.getLogger('pakit')


class Task(object):
    """
    The abstract metaclass interface that pakit uses to perform high
    level operations on a given system.

    The 'run' method performs the requested task.
    """
    __metaclass__ = ABCMeta

    def __str__(self):
        return self.name

    @property
    def name(self):
        """
        Just returns class name.
        """
        return self.__class__.__name__

    @abstractmethod
    def run(self):
        """
        Execute a set of operations to perform a Task.
        """
        raise NotImplementedError


class RecipeTask(Task):
    """
    Represents a task for a recipe.
    """
    def __init__(self, recipe):
        super(RecipeTask, self).__init__()
        if isinstance(recipe, Recipe):
            self.__recipe = recipe
        else:
            self.__recipe = RecipeDB().get(recipe)

    def __str__(self):
        return '{cls}: {recipe}'.format(cls=self.name,
                                        recipe=self.recipe.name)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.recipe.name != other.recipe.name:
            return False

        return True

    @property
    def recipe(self):
        """
        A reference to the associated recipe.
        """
        return self.__recipe

    def run(self):
        """
        Execute a set of operations to perform a Task.
        """
        raise NotImplementedError


class InstallTask(RecipeTask):
    """
    Build, link and verify a recipe on the host system.

    Does nothing if it is installed.
    """
    def __init__(self, recipe):
        super(InstallTask, self).__init__(recipe)

    def rollback(self, exc):
        """
        Handle the different types of execptions that may be raised during
        installation.

        Will always leave the system in a good state upon return.

        Args:
            exc: The exception that was raised.
        """
        USER.info('%s: Rolling Back Failed Build', self.recipe.name)
        cascade = False
        if isinstance(exc, AssertionError):
            logging.error('Error during verify() of %s', self.recipe.name)
            cascade = True
        if cascade or isinstance(exc, PakitLinkError):
            if not cascade:
                logging.error('Error during linking of %s', self.recipe.name)
            walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
            cascade = True
        if cascade or (not isinstance(exc, PakitLinkError) and
                       not isinstance(exc, AssertionError)):
            if not cascade:
                logging.error('Error during build() of %s', self.recipe.name)
            try:
                Command('rm -rf ' + self.recipe.install_dir).wait()
            except PakitCmdError:  # pragma: no cover
                pass

        # In all cases, remove the source code
        self.recipe.repo.clean()

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        entry = pakit.conf.IDB.get(self.recipe.name)
        if entry:
            msg = '{name}: Already Installed{nl}Repo: {repo}'
            msg += '{nl}Hash: {hash}{nl}Date: {date}'
            msg = msg.format(name=self.recipe.name, repo=entry['repo'],
                             hash=entry['hash'], date=entry['date'], nl=PREFIX)
            logging.debug(msg)
            print(msg)
            return

        try:
            USER.info('%s: Downloading: %s', self.recipe.name,
                      str(self.recipe.repo))
            with self.recipe.repo:
                USER.info('%s: Building Source', self.recipe.name)
                self.recipe.build()

                USER.info('%s: Symlinking Program', self.recipe.name)
                walk_and_link(self.recipe.install_dir, self.recipe.link_dir)

                USER.info('%s: Verifying Program', self.recipe.name)
                self.recipe.verify()

                pakit.conf.IDB.add(self.recipe)
        except Exception as exc:  # pylint: disable=W0703
            self.rollback(exc)
            raise


class RemoveTask(RecipeTask):
    """
    Remove a given recipe from the system.

    Does nothing if it is not installed.
    """
    def __init__(self, recipe):
        super(RemoveTask, self).__init__(recipe)

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        if pakit.conf.IDB.get(self.recipe.name) is None:
            print(self.recipe.name + ': Not Installed')
            return

        walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
        try:
            shutil.rmtree(self.recipe.install_dir)
        except OSError:  # pragma: no cover
            pass
        pakit.conf.IDB.remove(self.recipe.name)


class UpdateTask(RecipeTask):
    """
    Update a program, don't do it unless changes made.
    """
    def __init__(self, recipe):
        super(UpdateTask, self).__init__(recipe)
        self.back_dir = self.recipe.install_dir + '_bak'
        self.old_entry = None

    def save_old_install(self):
        """
        Before attempting an update of the program:
            - Unlink it.
            - Move the installation to a backup location.
            - Remove the pakit.conf.IDB entry.
        """
        USER.info('%s: Saving Old Install', self.recipe.name)
        walk_and_unlink(self.recipe.install_dir, self.recipe.link_dir)
        self.old_entry = pakit.conf.IDB.get(self.recipe.name)
        pakit.conf.IDB.remove(self.recipe.name)
        shutil.move(self.recipe.install_dir, self.back_dir)

    def restore_old_install(self):
        """
        The update failed, reverse the actions of save_old_install.
        """
        USER.info('%s: Restoring Old Install', self.recipe.name)
        shutil.move(self.back_dir, self.recipe.install_dir)
        pakit.conf.IDB.set(self.recipe.name, self.old_entry)
        walk_and_link(self.recipe.install_dir, self.recipe.link_dir)

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        USER.info('%s: Checking For Updates', self.recipe.name)
        cur_hash = pakit.conf.IDB.get(self.recipe.name)['hash']
        if cur_hash == self.recipe.repo.src_hash:
            return

        try:
            self.save_old_install()
            InstallTask(self.recipe).run()
            USER.info('%s: Deleting Old Install', self.recipe.name)
            Command('rm -rf ' + self.back_dir).wait()
        except Exception as exc:  # pylint: disable=W0703
            logging.error(exc)
            self.restore_old_install()


class DisplayTask(RecipeTask):
    """
    Display detailed information about a given recipe..
    """
    def __init__(self, recipe):
        super(DisplayTask, self).__init__(recipe)

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        logging.debug('Displaying Info: ' + self.recipe.name)

        msg = PREFIX[1:] + PREFIX.join(self.recipe.info().split('\n'))
        print(msg)
        return msg


class RelinkRecipes(Task):
    """
    Relink all programs managed by pakit.

    Useful if one Recipe adds something to another Recipe's install.
    Should be avoided unless absolutely necessary.

    For example, if you installed  python and used get-pip.py.
    It would modify pakit's python install, but have to be relinked to be used.
    """
    def __init__(self):
        super(RelinkRecipes, self).__init__()

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        logging.debug('Relinking All Programs')

        dst = pakit.conf.CONFIG.get('pakit.paths.link')
        Command('rm -rf ' + dst).wait()
        for _, recipe in RecipeDB():
            walk_and_link(recipe.install_dir, dst)


class ListInstalled(Task):
    """
    List all installed recipes.
    """
    def __init__(self, short=False):
        super(ListInstalled, self).__init__()
        self.short = short

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        logging.debug('List Installed Programs')
        if self.short:
            print(' '.join(sorted([ent for ent, _ in pakit.conf.IDB])))
            return

        nchars = 12
        fmt = str(nchars).join(['{prog:', '}   {repo:',
                                '}   {hash:', '}   {date}'])
        installed = ['Program        Repo           Hash           Date']
        installed.extend([fmt.format(prog=prog[0:nchars],
                                     repo=entry['repo'][0:nchars],
                                     date=entry['date'],
                                     hash=entry['hash'][0:nchars])
                          for prog, entry in pakit.conf.IDB])

        msg = 'Installed Programs:'
        msg += PREFIX + PREFIX.join(installed)
        print(msg)
        return msg


class ListAvailable(Task):
    """
    List all available recipes.
    """
    def __init__(self, short=False):
        super(ListAvailable, self).__init__()
        self.short = short

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
        logging.debug('List Available Recipes')
        if self.short:
            print(' '.join(RecipeDB().names(desc=False)))
            return

        available = ['Program      Description']
        available.extend(RecipeDB().names(desc=True))

        msg = 'Available Recipes:'
        msg += PREFIX + PREFIX.join(available)
        print(msg)
        return msg


def subseq_match(word, sequence):
    """
    Subsequence matcher, not case senstive.

    Args:
        word: The phrase under investigation.
        sequence: The sequence of ordered letters to look for.

    Returns:
        True iff the subsequence was present in the word.
    """
    seq = list(sequence.lower())
    for char in word.lower():
        if char == seq[0]:
            seq.remove(seq[0])
        if len(seq) == 0:
            return True
    return False


def substring_match(word, sequence):
    """
    Substring matcher, not case senstive.

    Args:
        word: The phrase under investigation.
        sequence: The substring to look for.

    Returns:
        True iff the substring was present in the word.
    """
    return word.lower().find(sequence.lower()) != -1


class SearchTask(Task):
    """
    Search the RecipeDB for matching recipes.
    """
    def __init__(self, words, queries):
        super(SearchTask, self).__init__()
        self.queries = queries
        self.words = words

    def run(self):
        """
        Execute a set of operations to perform the Task.
        """
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
