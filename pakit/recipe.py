# pylint: disable=W0212
""" The base class for build recipes. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import glob
import os

from pakit.shell import Command


class RecipeNotFound(Exception):
    """ The database can't find the requested recipe. """
    pass


class RecipeDB(object):
    """ Simple object database, allows queries and can search paths. """
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

    def update_db(self, path):
        """ Glob path, and update db with new recipes. """
        # TODO: Iterate all classes in file, only index subclassing Recipe
        new_recs = glob.glob(os.path.join(path, '*.py'))
        new_recs = [os.path.basename(fname)[0:-3] for fname in new_recs]
        if '__init__' in new_recs:
            new_recs.remove('__init__')

        mod = os.path.basename(path)
        for cls in new_recs:
            obj = self.__recipe_obj(mod, cls)
            self.__db.update({cls: obj})

    def get(self, name):
        """ Same as normal get, returns object or None if not found. """
        obj = self.__db.get(name)
        if obj is None:
            raise RecipeNotFound('Database missing entry: ' + name)
        return obj

    def names(self, **kwargs):
        """ Names of recipes available, optionally with descriptions. """
        if kwargs.get('desc', False):
            return sorted([str(recipe) for recipe in self.__db.values()])
        else:
            return sorted(self.__db.keys())

    def __recipe_obj(self, mod_name, cls_name):
        """ Return an instanciated object of cls_name. """
        mod = __import__('{mod}.{cls}'.format(mod=mod_name, cls=cls_name))
        mod = getattr(mod, cls_name)
        cls = getattr(mod, cls_name.capitalize())
        obj = cls()
        obj.set_config(self.__config)
        return obj


class Recipe(object):
    """ A schema to build some binary. """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self.desc = 'Short description for the recipe.'
        self.src = 'Source code url, will build bleeding edge version.'
        self.homepage = 'Project site'
        self.repos = {}
        self.opts = None

    def __enter__(self):
        self.repo.get_it()

    def __exit__(self, typ, value, traceback):
        pass

    def __str__(self):
        """ Short description. """
        return '{0:10}   {1}'.format(self.name[0:10], self.desc)

    def info(self):
        """ Long description of the recipe. """
        fmt = [
            '{name}',
            'Description: {desc}',
            'Homepage: {home}',
            'Current Repo: "{cur_build}"',
        ]
        for name, repo in sorted(self.repos.items()):
            fmt += ['Repo "' + name + '":', '{tab}' + str(repo)]
        fmt = '\n  '.join(fmt)
        info = fmt.format(name=self.name,
                          desc=self.desc,
                          home=self.homepage,
                          cur_build=self.repo_name,
                          tab='  ')
        return info.rstrip('\n')

    def set_config(self, config):
        """ Set the configuration for the recipe. """
        self.opts = config.get_opts(self.name)
        self.opts.update({
            'prefix': os.path.join(self.opts.get('prefix'), self.name),
            'source': os.path.join(self.opts.get('source'), self.name)
        })
        for repo in self.repos.values():
            repo.target = self.source_dir

    @property
    def install_dir(self):
        """ The folder the program will install to. """
        return self.opts.get('prefix')

    @property
    def link_dir(self):
        """ The folder the program will be linked to. """
        return self.opts.get('link')

    @property
    def source_dir(self):
        """ The folder where the source will download & build. """
        return self.opts.get('source')

    @property
    def name(self):
        """ The name of the recipe. """
        return self.__class__.__name__.lower()

    @property
    def repo(self):
        """ The repository to build from. """
        return self.repos.get(self.repo_name)

    @repo.setter
    def repo(self, new_repo):
        """ Set the repository to build from. """
        if new_repo not in self.repos:
            raise KeyError('Build repository not available.')
        self.opts['repo'] = new_repo

    @property
    def repo_name(self):
        """ Return the name of the repository being used. """
        return self.opts.get('repo')

    def cmd(self, cmd_str, cmd_dir=None):
        """ Execute a given cmd_str on the system.

            cmd_str: A string that gets formatted with self.opts.
            cmd_dir: A directory to execute in.
        """
        # FIXME: Temporary hack, need to refactor cmd function.
        if cmd_dir is None:
            cmd_dir = self.source_dir

        # TODO: Later, pickup opts from config & extend with prefix.
        cmd_str = cmd_str.format(**self.opts)
        cmd = Command(cmd_str, cmd_dir)
        cmd.wait()

        return cmd.output()

    @abstractmethod
    def build(self):
        """ Build the program. """
        raise NotImplementedError

    @abstractmethod
    def verify(self):
        """ Verify it works somehow. """
        raise NotImplementedError
