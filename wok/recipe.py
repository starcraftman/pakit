""" The base class for build recipes. """
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod

import glob
import os

from wok.shell import Command, Git

class RecipeNotFound(Exception):
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
        cls.__instance.__default_formulas()
        return cls.__instance

    def __str__(self):
        progs = ['\n- {0}'.format(str(prog)) for prog in self.__db.values()]
        return 'Available To Install: ' + ''.join(progs)

    def update_db(self, path):
        """ Glob path, and update db with new recipes. """
        # TODO: Iterate all classes in file, only index those subclassing Recipe
        new_recs = glob.glob(os.path.join(path, '*.py'))
        new_recs = [os.path.basename(fname)[0:-3] for fname in new_recs]
        new_recs.remove('__init__')

        mod = os.path.basename(path)
        for cls in new_recs:
            obj = self.__recipe_obj(mod, cls)
            self.__db.update({cls: obj})

    def has(self, name):
        return name in self.__db

    def get(self, name):
        obj = self.__db.get(name)
        if obj is None:
            raise RecipeNotFound('Database missing entry: ' + name)
        return obj

    def names(self):
        """ Names of recipes available. """
        return self.__db.keys()

    def names_and_desc(self):
        """ Names and descriptions available. """
        return [str(recipe) for recipe in self.__db.values()]

    def __default_formulas(self):
        """ Populate the default formulas. """
        def_formulas = __file__
        for _ in range(0, 2):
            def_formulas = os.path.dirname(def_formulas)
        def_formulas = os.path.join(def_formulas, 'formula')
        self.update_db(def_formulas)

    def __recipe_obj(self, mod_name, cls_name):
        """ Return an instanciated object of cls_name. """
        mod = __import__('{mod}.{cls}.'.format(mod=mod_name, cls=cls_name))
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
        self.stable = None
        self.unstable = None

    def __str__(self):
        """ Short description. """
        return self.name + ': ' + self.desc

    def info(self):
        """ Long description. """
        return '{desc}{nl}{home}{nl}Stable Build:{nl}  {stable}{nl}Unstable Build:{nl}  {unstable}'.format(
                desc=str(self), nl='\n  ', home='Homepage: ' + self.homepage,
                stable=str(self.stable), unstable=str(self.unstable)
                )

    def set_config(self, config):
        self.paths = config.get('paths')
        if self.unstable is not None:
            self.unstable.target = self.source_dir
        if self.stable is not None:
            self.stable.target = self.source_dir

    @property
    def install_dir(self):
        return os.path.join(self.paths.get('prefix'), self.name)

    @property
    def link_dir(self):
        return self.paths.get('link')

    @property
    def source_dir(self):
        return os.path.join(self.paths.get('source'), self.name)

    @property
    def name(self):
        return self.__class__.__name__.lower()

    def cmd(self, cmd_str, cmd_dir=None):
        # FIXME: Temporary hack, need to refactor cmd function.
        if cmd_dir is None:
            if os.path.exists(self.source_dir):
                cmd_dir = self.source_dir
            else:
                cmd_dir = os.path.dirname(self.link_dir)

        # TODO: Later, pickup opts from config & extend with prefix.
        opts = {'link': self.link_dir, 'prefix': self.install_dir,
                'source': self.source_dir}
        cmd_str = cmd_str.format(**opts)
        cmd = Command(cmd_str, cmd_dir)
        cmd.wait()

        return cmd.output()

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
