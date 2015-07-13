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
        return 'Available Programs: ' + str(self.__db.keys())

    def __default_formulas(self):
        """ Populate the default formulas. """
        def_formulas = __file__
        for _ in range(0, 2):
            def_formulas = os.path.dirname(def_formulas)
        def_formulas = os.path.join(def_formulas, 'formula')
        self.update_db(def_formulas)

    def update_db(self, path):
        """ Glob path, and update db with new recipes. """
        new_recs = glob.glob(os.path.join(path, '*.py'))
        new_recs = [os.path.basename(fname)[0:-3] for fname in new_recs]
        new_recs.remove('__init__')

        mod = os.path.basename(path)
        for cls in new_recs:
            obj = self.__recipe_obj(mod, cls)
            self.__db.update({cls: obj})

    def __recipe_obj(self, mod_name, cls_name):
        """ Return an instanciated object of cls_name. """
        mod = __import__('{mod}.{cls}.'.format(mod=mod_name, cls=cls_name))
        mod = getattr(mod, cls_name)
        cls = getattr(mod, cls_name.capitalize())
        obj = cls()
        obj.set_config(self.__config)
        return obj

    def available(self):
        return self.__db.keys()

    def has(self, name):
        return self.__db.has_key(name)

    def get(self, name):
        obj = self.__db.get(name)
        if obj is None:
            raise RecipeNotFound('Database missing entry: ' + name)
        return obj

    def search(self, sequence):
        """ Search all available for matches to subsequence. """
        matched = []
        for name in self.available():
            if self.__seq_match(name, sequence):
                matched.append(name)

        return matched

    def __seq_match(self, word, sequence):
        """ Subsequence matcher. """
        seq = list(sequence)
        for char in word:
            if char == seq[0]:
                seq.remove(seq[0])
            if len(seq) == 0:
                return True

        return False

class Recipe(object):
    """ A schema to build some binary. """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self.desc = 'Short description for the recipe.'
        self.src = 'Source code url, will build bleeding edge version.'
        self.homepage = 'Project site'
        self.paths = None
        self.stable = None
        self.unstable = None

    def set_paths(self, paths):
        self.paths = paths

    def set_config(self, config):
        self.paths = config.paths
        if self.unstable is not None:
            self.unstable.target = self.source_dir()
        if self.stable is not None:
            self.stable.target = self.source_dir()

    def install_dir(self):
        return os.path.join(self.paths.get('prefix'), self.name())

    def link_dir(self):
        return self.paths.get('link')

    def source_dir(self):
        return os.path.join(self.paths.get('source'), self.name())

    def name(self):
        return self.__class__.__name__.lower()

    def cmd(self, cmd_str, cmd_dir=None):
        # FIXME: Temporary hack, need to refactor cmd function.
        if cmd_dir is None:
            if os.path.exists(self.source_dir()):
                cmd_dir = self.source_dir()
            else:
                cmd_dir = os.path.dirname(self.link_dir())

        # TODO: Later, pickup opts from config & extend with prefix.
        opts = {'link': self.link_dir(), 'prefix': self.install_dir(),
                'source': self.source_dir()}
        cmd_str = cmd_str.format(**opts)
        cmd = Command(cmd_str, cmd_dir)
        cmd.wait()

        return cmd.output()

    def download(self):
        """ Git source checkout. """
        repo = Git(self.src, target=self.source_dir())
        repo.download()

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
