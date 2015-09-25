# pylint: disable=W0212
"""
The Recipe class and RecipeDB are found here.

Recipe: The base class for all recipes.
RecipeDB: The database that indexes all recipes.
"""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import glob
import logging
import os
import sys

from pakit.exc import PakitDBError
from pakit.shell import Command


class Recipe(object):
    """
    A recipe to build some binary through a series of commands.

    *description* and *more_info* are based on the class's __doc__ string.
        description: The first non blank line in __doc__
        more_info: The second non blank line to end of __doc__

    Attributes:
        description: A short description that summarizes the recipe.
            Keep it short, less than 50 chars suggested.
        more_info: A longer description, may take several lines.
        homepage: The website that hosts the project.
        repos: A dictionary that stores all possible methods to retrieve
            source code. By convention, should contain a *stable* and
            *unstable* entry.
        opts: A dictionary storing options for the recipe, to be
            used primarily in the build() commands. See 'cmd' method.
        repo: The active source repository.
        repo_name: The name of the current repository in *repos*.
        name: The name of the recipe.
        install_dir: Where the program will be installed to.
        link_dir: Where the installation will be linked to.
        source_dir: Where the source code will be downloaded to and built.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self.def_cmd_dir = None
        self.homepage = None
        self.opts = {}
        self.repos = None

    def __str__(self):
        """
        A one line summary of the recipe.
        """
        return '{0:10}   {1}'.format(self.name[0:10], self.description)

    def info(self):
        """
        A detailed description of the recipe.
        """
        tab = '  '
        fmt = [
            '{name}',
            'Description: {desc}',
            'Homepage: {home}',
            'Current Repo: "{cur_repo}"',
        ]
        for name, repo in sorted(self.repos.items()):
            fmt += ['Repo "' + name + '":', '{tab}' + str(repo)]
        if self.more_info:
            fmt += ['More Information:']
            fmt += [tab + line for line in self.more_info]
        fmt = '\n  '.join(fmt)
        info = fmt.format(name=self.name,
                          desc=self.description,
                          home=self.homepage,
                          cur_repo=self.repo_name,
                          tab=tab)
        return info.rstrip('\n')

    def set_config(self, config):
        """
        Query the config for the required opts.

        Users should not be using this directly.
        """
        self.opts = config.get_opts(self.name)
        self.opts.update({
            'prefix': os.path.join(self.opts.get('prefix'), self.name),
            'source': os.path.join(self.opts.get('source'), self.name)
        })
        for repo in self.repos.values():
            repo.target = self.source_dir

    @property
    def description(self):
        """
        Return a one line description of the program.
        """
        lines = [line for line in self.__doc__.split('\n') if line != '']

        return lines[0].strip()

    @property
    def more_info(self):
        """
        Return a longer description of the program.
        """
        first_non_blank = True
        rest = None
        lines = self.__doc__.split('\n')

        # Start at second non blank line
        for num, line in enumerate(lines):
            line = line.strip()
            if line and first_non_blank:
                first_non_blank = False
                continue
            if line:
                rest = [sline.strip() for sline in lines[num:]]
                break

        # Remove trailing blank lines
        if rest:
            index = len(rest)
            reversed_rest = list(reversed(rest))
            for num, line in enumerate(reversed_rest):
                if line:
                    index = num
                    break
            rest = list(reversed(reversed_rest[index:]))

        return rest

    @property
    def install_dir(self):
        """
        The folder the program will install to.
        """
        return self.opts.get('prefix')

    @property
    def link_dir(self):
        """
        The folder the program will be linked to.
        """
        return self.opts.get('link')

    @property
    def source_dir(self):
        """
        The folder where the source will download & build.
        """
        return self.opts.get('source')

    @property
    def name(self):
        """
        The name of the recipe.
        """
        return self.__class__.__name__.lower()

    @property
    def repo(self):
        """
        The *Fetchable* class providing the source code.
        """
        return self.repos.get(self.repo_name)

    @repo.setter
    def repo(self, new_repo):
        """
        Set the repository for the source code.

        Args:
            new_repo: A key in *repos*.
        """
        if new_repo not in self.repos:
            raise KeyError('Build repository not available.')
        self.opts['repo'] = new_repo
        if os.path.exists(self.source_dir):
            self.repo.clean()

    @property
    def repo_name(self):
        """
        The name of the repository in *repos*.
        """
        return self.opts.get('repo')

    def cmd(self, cmd, **kwargs):
        """
        Wrapper around pakit.shell.Command. Behaves the same except:

        - Expand all dictionary markers in *cmd* against *self.opts*.
            Arg *cmd* may be a string or a list of strings.
        - If no *cmd_dir* in kwargs, use default from *def_cmd_dir*.

        Returns:
            Command object that is running in a subprocess.
        """
        if isinstance(cmd, type('')):
            cmd = cmd.format(**self.opts)
        else:
            cmd = [word.format(**self.opts) for word in cmd]

        if kwargs.get('cmd_dir') is None:
            kwargs.update({'cmd_dir': self.def_cmd_dir})

        logging.getLogger('pakit').info('Executing in %s: %s',
                                        kwargs['cmd_dir'], cmd)
        cmd = Command(cmd, **kwargs)
        cmd.wait()
        return cmd

    @abstractmethod
    def build(self):
        """
        Build the program from the source directory.

        Should make use of the 'cmd' method to execute system commands.

        Can put build specific commands based on repo_name.

        Raises:
            PakitCmdError: A Command returned an error.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self):
        """
        Use `assert` statements to verify the built program works.

        Raises:
            AssertionError: When an assertion fails.
        """
        raise NotImplementedError


class RecipeDB(object):
    """
    An object database that can import recipes dynamically.
    """
    __instance = None

    def __new__(cls, config=None):
        """ Used to implement singleton. """
        if cls.__instance is None:
            cls.__instance = super(RecipeDB, cls).__new__(cls)
            cls.__instance.__db = {}
            if config is not None:
                cls.__instance.__config = config
        return cls.__instance

    def __contains__(self, name):
        return name in self.__db

    def index(self, path):
        """
        Index all *Recipes* in the path.

        For each file, the Recipe subclass should be named after the file.
        So for path/ag.py should have a class called Ag.

        Args:
            path: The folder containing recipes to index.
        """
        # TODO: Iterate all classes in file, only index subclassing Recipe
        sys.path.insert(0, os.path.dirname(path))

        new_recs = glob.glob(os.path.join(path, '*.py'))
        new_recs = [os.path.basename(fname)[0:-3] for fname in new_recs]
        if '__init__' in new_recs:
            new_recs.remove('__init__')

        mod = os.path.basename(path)
        for cls in new_recs:
            obj = self.__recipe_obj(mod, cls)
            self.__db.update({cls: obj})

        sys.path = sys.path[1:]

    def get(self, name):
        """
        Get the recipe from the database.

        Raises:
            PakitDBError: Could not resolve the name to a recipe.
        """
        obj = self.__db.get(name)
        if obj is None:
            raise PakitDBError('Missing recipe to build: ' + name)
        return obj

    def names(self, desc=False):
        """
        Names of recipes available, optionally with descriptions.

        Args:
            desc:
                When True, return a list of recipe names and descriptions.
                When False, return a list of recipe names and descriptions.

        Returns:
            A list of strings. By default the names of all recipes.
            Otherwise, it is a list of recipes and their description.
        """
        if desc:
            return sorted([str(recipe) for recipe in self.__db.values()])
        else:
            return sorted(self.__db.keys())

    def __recipe_obj(self, mod_name, cls_name):
        """
        Import and instantiate the recipe class. Then configure it.

        Args:
            mod_name: The module name, should be importable via PYTHONPATH.
            cls_name: The class name in the module.

        Returns:
            The instantiated recipe.

        Raises:
            ImportError: If the module could not be imported.
            AttributeError: The module did not have the required class.
        """
        mod = __import__('{mod}.{cls}'.format(mod=mod_name, cls=cls_name))
        mod = getattr(mod, cls_name)
        cls = getattr(mod, cls_name.capitalize())
        obj = cls()
        obj.set_config(self.__config)
        return obj
