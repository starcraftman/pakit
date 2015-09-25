"""
All configuration of pakit is done here.

Config: Handles global configuration of pakit.
InstallDB: Handles the database of installed programs.
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
            'recipes': os.path.expanduser('~/.pakit/recipes'),
            'source': '/tmp/pakit/src',
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
    The main configuration file, users can modify global behaviour here.

    For example, after parsing the YAML the config may hold:
        config = {
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
                    'recipes': '/home/username/.pakit/recipes',
                    'source': '/tmp/pakit/src',
                },
            },
            'ag': {
                'repo': 'unstable'
            }
        }

    Details:

    pakit.command.timeout
        The timeout for commands.
        When no stdout produced for timeout kill process.

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
        Path to a folder with user created recipes.
        Path must be a valid package name that can be imported.
        Importantly this means base folder
        can NOT be a hidden directory (leading '.').

    pakit.paths.source
        The path where source code will be downloaded & built.

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
        self.__conf = copy.deepcopy(TEMPLATE)
        if os.path.exists(self.filename):
            self.read()

    def __str__(self):
        pretty_js = json.dumps(self.__conf, sort_keys=True, indent=2)
        pretty_js = '\n'.join([line.rstrip() for line
                               in pretty_js.split('\n')])
        return 'Config File: {fname}\nContents:\n{jso}'.format(
            fname=self.filename, jso=pretty_js)

    def __contains__(self, key_str):
        obj = self.__conf
        for key in key_str.split('.'):
            logging.error(key)
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
        obj = self.__conf
        leaf = key_str.split('.')[-1]
        try:
            for key in key_str.split('.')[0:-1]:
                obj = obj[key]
        except KeyError:
            obj = TEMPLATE
            for key in key_str.split('.')[0:-1]:
                obj = obj[key]

        return obj[leaf]

    def get_opts(self, recipe_name):
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

    def reset(self):
        """
        Reset the config to default.
        """
        self.__conf = copy.deepcopy(TEMPLATE)

    def set(self, key_str, val):
        """
        Modify the underlying config, will create nodes if needed.

        Args:
            key: A period separated path down the config dictionary.
                For example `pakit.paths.prefix`, would be equivalent
                to conf['pakit']['paths']['prefix'].
            val: The value to assign to the key.
        """
        obj = self.__conf
        leaf = key_str.split('.')[-1]
        for key in key_str.split('.')[0:-1]:
            new_obj = obj.get(key, None)
            if new_obj is None:
                obj[key] = dict()
                new_obj = obj.get(key)
            obj = new_obj
        obj[leaf] = val

    def read(self):
        """
        Read the config into memory.
        """
        self.__conf = self.read_from()

    def write(self):
        """
        Write the config to the file.
        """
        self.write_to(self.__conf)


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
        self.__conf = {}
        if os.path.exists(self.filename):
            self.read()

    def __str__(self):
        pretty_js = json.dumps(self.__conf, sort_keys=True, indent=2)
        pretty_js = '\n'.join([line.rstrip() for line
                               in pretty_js.split('\n')])
        return 'Config File: {fname}\nContents:\n{jso}'.format(
            fname=self.filename, jso=pretty_js)

    def __iter__(self):
        for key in sorted(self.__conf):
            yield (key, copy.deepcopy(self.__conf[key]))

    def __contains__(self, key):
        return key in self.__conf

    def get(self, prog):
        """
        Get the entry for prog.

        Returns;
            A dictionary containing the information on *prog*.
            If not present, returns None.
        """
        return self.__conf.get(prog)

    def set(self, key, value):
        """
        Set the *key* in the database to *value*.
        """
        self.__conf[key] = value

    def add(self, recipe):
        """
        Update the database for recipe.

        Args:
            recipe: The Recipe object to add to the database.
        """
        time_s = time.time()
        self.__conf[recipe.name] = {
            'date': time.strftime('%H:%M:%S %d/%m/%y', time.localtime(time_s)),
            'hash': recipe.repo.src_hash,
            'repo': recipe.repo_name,
            'timestamp': time_s,
        }
        self.write()

    def remove(self, prog):
        """
        Remove *prog* from the database.
        """
        del self.__conf[prog]
        self.write()

    def read(self):
        """
        Read the config into memory.
        """
        self.__conf = self.read_from()

    def write(self):
        """
        Write to the config file.
        """
        self.write_to(self.__conf)
