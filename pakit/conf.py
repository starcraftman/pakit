"""
All configuration of pakit is done here.

YamlMixin: A mixin class that can read/write yaml files.
Config: Handles global configuration of pakit.
InstallDB: Handles the database of installed programs.
RecipeURIDB: Store and track recipe URIs.
"""
from __future__ import absolute_import

import copy
import json
import logging
import os
import time
import yaml

CONFIG = None
IDB = None
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


class YamlMixin(object):
    """
    A mixin class to read and write YAML files.

    Attributes:
        filename: The file that holds the config.
    """

    def __init__(self, filename):
        super(YamlMixin, self).__init__()
        self.__filename = filename

    @property
    def filename(self):
        """
        The config file.
        """
        return self.__filename

    @filename.setter
    def filename(self, new_filename):
        """
        Set the config file.
        """
        if not os.path.exists(new_filename):
            logging.error('File not found: %s', new_filename)
        self.__filename = new_filename

    def read_from(self):
        """
        Read the config file into a python object.

        Returns:
            A dict containing the contents of the entire nested
            YAML file.
        """
        try:
            with open(self.filename) as fin:
                conf = yaml.load(fin)

            pretty_js = json.dumps(conf, sort_keys=True, indent=2)
            msg = 'Config File: {fname}\nContents:\n{jso}'.format(
                fname=self.filename, jso=pretty_js)
            logging.debug(msg)
            return conf
        except IOError as exc:
            logging.error('Failed to load user config. %s', exc)

    def write_to(self, obj):
        """
        Write the contents of a python dictionary to the config file.

        Args:
            obj: An arbitrarily filled python dictionary.
        """
        with open(self.filename, 'w') as fout:
            yaml.dump(obj, fout, default_flow_style=False)
            logging.info('Config written to: %s', self.filename)


class Config(YamlMixin):
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
        super(Config, self).__init__(filename)
        self.conf = copy.deepcopy(TEMPLATE)
        if os.path.exists(self.filename):
            self.read()

    def __str__(self):
        pretty_js = json.dumps(self.conf, sort_keys=True, indent=2)
        pretty_js = '\n'.join([line.rstrip() for line
                               in pretty_js.split('\n')])
        return 'Config File: {fname}\nContents:\n{jso}'.format(
            fname=self.filename, jso=pretty_js)

    def __contains__(self, key_str):
        obj = self.conf
        for key in key_str.split('.'):
            if key not in obj:
                return False
            obj = obj[key]

        return True

    def get(self, key_str):
        """
        Get the value of a key from config dictionary.

        Args:
            key_str: A period separated path down the config dictionary.
                For example `pakit.paths.prefix`, would be equivalent
                to config['pakit']['paths']['prefix']

        Returns:
            The object stored at *key*.

        Raises:
            KeyError: The key does not exist.
        """
        obj = self.conf
        leaf = key_str.split('.')[-1]
        try:
            for key in key_str.split('.')[0:-1]:
                obj = obj[key]
        except KeyError:
            obj = TEMPLATE
            for key in key_str.split('.')[0:-1]:
                obj = obj[key]

        return obj[leaf]

    def reset(self):
        """
        Reset the config to default.
        """
        self.conf = copy.deepcopy(TEMPLATE)

    def set(self, key_str, val):
        """
        Modify the underlying config, will create nodes if needed.

        Args:
            key: A period separated path down the config dictionary.
                For example `pakit.paths.prefix`, would be equivalent
                to conf['pakit']['paths']['prefix'].
            val: The value to assign to the key.
        """
        obj = self.conf
        leaf = key_str.split('.')[-1]
        for key in key_str.split('.')[0:-1]:
            new_obj = obj.get(key, None)
            if new_obj is None:
                obj[key] = dict()
                new_obj = obj.get(key)
            obj = new_obj
        obj[leaf] = val

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
        opts = copy.deepcopy(self.get('pakit.defaults'))
        opts.update(self.get('pakit.paths'))
        try:
            opts.update(self.get(recipe_name))
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
        return self.get('pakit.paths.' + key)

    def read(self):
        """
        Read the config into memory.
        """
        self.conf = self.read_from()

    def write(self):
        """
        Write the config to the file.
        """
        self.write_to(self.conf)


class InstallDB(YamlMixin):
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
        self.conf = {}
        if os.path.exists(self.filename):
            self.read()

    def __str__(self):
        pretty_js = json.dumps(self.conf, sort_keys=True, indent=2)
        pretty_js = '\n'.join([line.rstrip() for line
                               in pretty_js.split('\n')])
        return 'Config File: {fname}\nContents:\n{jso}'.format(
            fname=self.filename, jso=pretty_js)

    def __iter__(self):
        for key in sorted(self.conf):
            yield (key, copy.deepcopy(self.conf[key]))

    def __contains__(self, key):
        return key in self.conf

    def __delitem__(self, key):
        self.remove(key)

    def __getitem__(self, key):
        return self.conf[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def get(self, key, default=None):
        """
        Get the entry for key.

        Returns;
            A dictionary containing the information associated with key*.
            If not present, returns None.
        """
        return self.conf.get(key, default)

    def set(self, key, value):
        """
        Set the *key* in the database to *value*.
        """
        self.conf[key] = value

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

    def remove(self, recipe):
        """
        Remove recipe from the database.
        """
        del self.conf[recipe]
        self.write()

    def read(self):
        """
        Read the config into memory.
        """
        self.conf = self.read_from()

    def write(self):
        """
        Write to the config file.
        """
        self.write_to(self.conf)


class RecipeURIDB(InstallDB):
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
        existing = [self[key]['path'] for key in self.conf]
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
        for uri in self.conf:
            remote = self[uri]
            if remote['is_vcs'] and (time.time() - remote['time']) > interval:
                to_update.append(uri)

        return to_update
