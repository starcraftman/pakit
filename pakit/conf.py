"""
All configuration of pakit is done here.

YamlDict: A dictionary class similar to UserDict, can be serialized
          to/from Yaml.
YamlNestedDict: Same as YamlDict for convenient nesting.
Config: Handles global configuration of pakit.
InstallDB: Handles the database of installed programs.
RecipeURIDB: Store and track recipe URIs.
"""
from __future__ import absolute_import

import copy
import json
import logging
import os
import tempfile
import time
from collections import MutableMapping

import yaml

CONFIG = None
IDB = None
TMP_DIR = tempfile.mkdtemp(prefix='pakit_cmd_stdout_')
TEMPLATE = {
    'pakit': {
        'command': {
            'timeout': 120
        },
        'defaults': {
            'repo': 'stable',
        },
        'log': {
            'enabled': True,
            'file': '/tmp/pakit/main.log',
            'level': 'debug',
        },
        'paths': {
            'link': '/tmp/pakit/links',
            'prefix': '/tmp/pakit/builds',
            'recipes': os.path.expanduser('~/.pakit'),
            'source': '/tmp/pakit/src',
        },
        'recipe': {
            'update_interval': 60 * 60 * 24,
            'uris': [
                {'uri': 'https://github.com/pakit/base_recipes'},
                {'uri': 'user_recipes'},
            ],
        },
    },
}


class YamlDict(MutableMapping):
    """
    A custom dictionary with special features:
        - Essentially like UserDict
        - Written to self.filename with write()
        - Loads arbitrary dictionary obj into self.data with read()
    """
    def __init__(self, fname=None, default_data=None):
        self.data = {}
        self.filename = fname
        if self.filename and os.path.exists(self.filename):
            self.read()
        elif default_data:
            self.data.update(default_data)

    def __getitem__(self, key_str):
        return self.data[key_str]

    def __setitem__(self, key_str, new_val):
        self.data[key_str] = new_val

    def __delitem__(self, key_str):
        del self.data[key_str]

    def __iter__(self):
        for key in sorted(self.data):
            yield key

    def __len__(self):
        return len(self.data)

    def __str__(self):
        prefix = 'Class: ' + self.__class__.__name__ + os.linesep
        prefix += 'Filename: ' + self.filename + os.linesep
        return prefix + json.dumps(self.data, sort_keys=True,
                                   separators=(',', ': '), indent=2)

    def remove(self, key):
        """
        Simple convenience method for removing entries.
        """
        del self[key]

    def read(self):
        """
        Read the config file into a python object.
        """
        try:
            with open(self.filename) as fin:
                self.data = yaml.load(fin)
            logging.debug(self)
        except IOError as exc:
            logging.error('Failed to load user config. %s', exc)

    def write(self):
        """
        Write the contents of a python dictionary to the config file.

        Args:
            obj: An arbitrarily filled python dictionary.
        """
        with open(self.filename, 'w') as fout:
            yaml.dump(self.data, fout, default_flow_style=False)
            logging.info('Config written to: %s', self.filename)


class YamlNestedDict(YamlDict):
    """
    Same as YamlDict except:
        - Allows nested dictionary shorthand,
          i.e. dict['a.b.c'] = dict['a']['b']['c']
    """
    def __init__(self, fname=None, default_data=None):
        super(YamlNestedDict, self).__init__(fname, default_data)

    def __getitem__(self, key_str):
        obj = self.data
        keys = key_str.split('.')
        leaf = keys[-1]

        for key in keys[0:-1]:
            obj = obj[key]
        return obj[leaf]

    def __setitem__(self, key_str, new_val):
        obj = self.data
        keys = key_str.split('.')
        leaf = keys[-1]

        for key in keys[0:-1]:
            try:
                obj = obj[key]
            except KeyError:
                obj[key] = {}
                obj = obj[key]

        obj[leaf] = new_val

    def __delitem__(self, key_str):
        obj = self.data
        keys = key_str.split('.')
        leaf = keys[-1]

        for key in keys[0:-1]:
            obj = obj[key]
        del obj[leaf]


class Config(YamlNestedDict):
    """
    The main configuration class, users can modify global behaviour here.

    The yaml file is read and mapped to a tiered python dictionary.
    See pakit.conf.TEMPLATE for the defaults.

    Details of config:

    pakit.command.timeout
        The timeout for commands.
        When no stdout produced for timeout seconds kill the process.

    pakit.log.enabled
        Toggles the file logger. Console errors are always enabled.

    pakit.log.file
        Where the file log will be written to.

    pakit.log.level
        The level to write to the file log.

    pakit.paths.link
        Path where all programs will be linked to.
        You should put the bin folder in this folder on the `$PATH`.
        For the above config, `PATH=/tmp/pakit/links/bin:$PATH`.

    pakit.paths.prefix
        All recipes will be installed inside their own silos here.
        Using the above config, the recipe `ag` would be
        installed under `/tmp/pakit/builds/ag`.

    pakit.paths.recipes
        Path to a folder where all recipes will be stored.
        All recipes will be specified in the `pakit.recipe.uris` node.

    pakit.paths.source
        The path where source code will be downloaded & built.

    pakit.recipe.update_interval
        After a recipe uri has not been updated for update_interval seconds
        check for updates.

    pakit.recipe.uris
        The list contains a series of dictionaries that specify recipes.
        Recipes are indexed in the order of the list.
        Each dictionary must contain the 'uri' key as described below.
        Any other keys will be passed to pakit.shell.vcs_factory as kwargs.
        Remotely fetched recipes will be periodically updated.

        The 'uri' key must be one of ...

        - A version control uri supported by `pakit.shell.vcs_factory`
          like git or mercurial.
        - A simple folder name to be used in `pakit.paths.recipes`.

    pakit.defaults
        A dictionary of default options made available to all recipes.
        Anything in this, will be available inside recipes as self.opts.

    pakit.defaults.repo
        The default source repository to use.
        By convention, "stable" should always fetch a stable versioned release.
        Whereas "unstable" should build from recent project commits.

    ag
        A recipe specific dictionary that will override keys of the same
        name in `pakit.defaults`.

    ag.repo
        Setting "unstable" here overrides the value of "pakit.defaults.repo".

    Attributes:
        filename: The file that holds the config.
    """
    def __init__(self, filename):
        super(Config, self).__init__(filename, copy.deepcopy(TEMPLATE))

    def get(self, *args):
        """
        Same as normal dictionary get, except that when default not provided
        the value from TEMPLATE will be returned.

        Returns:
            The object stored at *key*.

        Raises:
            KeyError: The key did not exist in base TEMPLATE
        """
        key = args[0]
        try:
            return self[key]
        except KeyError:
            if len(args) > 1:
                return args[1]
            else:
                ydict = YamlNestedDict()
                ydict.data = TEMPLATE
                return ydict[key]

    def reset(self):
        """
        Reset the config to default.
        """
        self.data = copy.deepcopy(TEMPLATE)

    def opts_for(self, recipe_name):
        """
        Retrieves from config all options needed for *recipe_name*.

        Args:
            recipe_name: The recipe to look for.

        Returns:
            A dictionary that starts with everything under
            config['pakit']['defaults'] and updates the dictionary
            with the values in:
                - config['pakit']['paths']
                - config[recipe_name]
        """
        opts = copy.deepcopy(self['pakit.defaults'])
        opts.update(self['pakit.paths'])
        try:
            opts.update(self[recipe_name])
        except KeyError:
            pass
        return opts

    def path_to(self, key):
        """
        Get the path to ...

        Args:
            key: A key in `pakit.paths` dictionary.

        Returns:
            The specific path requested.

        Raises:
            KeyError: The key was not present.
        """
        return self['pakit.paths.' + key]


class InstallDB(YamlDict):
    """
    Used internally to store information about installed programs.

    Each program will have its own dictionary containing:
        - the date built
        - the repo source code was retrieved from
        - the hash of the build

    Attributes:
        filename: The file that holds the config.
    """
    def __init__(self, filename):
        super(InstallDB, self).__init__(filename)

    def add(self, *args):
        """
        Update the database for recipe.
        Handles some internal entries like timestamps.

        Args:
            recipe: The Recipe object to add to the database.
        """
        recipe = args[0]
        timestamp = time.time()
        self[recipe.name] = {
            'date': time.strftime('%H:%M:%S %d/%m/%y',
                                  time.localtime(timestamp)),
            'hash': recipe.repo.src_hash,
            'repo': recipe.repo_name,
            'time': timestamp,
        }
        self.write()


class RecipeURIDB(YamlDict):
    """
    Store information on configured recipe uris and the paths to index them.
    """
    def __init__(self, filename):
        super(RecipeURIDB, self).__init__(filename)

    def add(self, *args):
        """
        Add an entry to the database based on the uri.
        Will overwrite the entry if it exists in the database prior.

        Args:
            uri: A uri that is unique in the database.
            path: An absolute path to the recipes.
            is_vcs: True if and only if it is a version control repository.
            kwargs: Optional, a dict of kwargs for the vcs_factory.
        """
        uri, path, is_vcs = args[0], args[1], args[2]
        kwargs = args[3] if len(args) == 4 else None
        self[uri] = {
            'is_vcs': is_vcs,
            'path': path,
        }
        if isinstance(kwargs, type({})) and len(kwargs):
            self[uri]['kwargs'] = kwargs
        self.update_time(uri)

    def update_time(self, uri):
        """
        Update the timestmap on a uri in the database.

        Args:
            uri: A valid uri in the database.
        """
        timestamp = time.time()
        self[uri].update({
            'date': time.strftime('%H:%M:%S %d/%m/%y',
                                  time.localtime(timestamp)),
            'time': timestamp,
        })

    def select_path(self, preferred):
        """
        Select a path that is unique within the database.

        Args:
            preferred: The preferred path.

        Returns:
            The selected path that is unique in the database.
        """
        existing = [self[key]['path'] for key in self]
        new_path = preferred
        cnt = 0
        while new_path in existing:
            cnt += 1
            new_path = preferred + '_' + str(cnt)

        return new_path

    def need_updates(self, interval):
        """
        Returns a list of uris that should be updated because they are older
        than the supplied interval.

        Args:
            interval: A number of seconds, uris that haven't been updated
                in this interval will be selected.
        """
        to_update = []
        for uri in self:
            remote = self[uri]
            if remote['is_vcs'] and (time.time() - remote['time']) > interval:
                to_update.append(uri)

        return to_update
