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
import yaml  # pylint: disable=F0401

TEMPLATE = {
    'defaults': {
        'repo': 'stable',
    },
    'paths': {
        'link': '/tmp/pakit/links',
        'prefix': '/tmp/pakit/builds',
        'recipes': os.path.expanduser('~/.pakit/recipes'),
        'source': '/tmp/pakit/src',
    },
    'log': {
        'enabled': True,
        'file': '/tmp/pakit/main.log',
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


class Config(YamlMixin, object):
    """
    The main configuration file, users can modify global behaviour here.

    Global default should be found at:  ~/.pakit.yaml

    For example, after parsing the YAML the config may hold:
        config = {
            'defaults': {
                'repo': 'stable',
            },
            'paths': {
                'link': '/tmp/pakit/links',
                'prefix': '/tmp/pakit/builds',
                'source': '/tmp/pakit/src',
            },
            'log': {
                'enabled': True,
                'file': '/tmp/pakit/main.log',
            },
            'ag': {
                'repo': 'unstable'
            }
        }

    Details:
      'paths.link'     the path you should put on your $PATH.
            All programs will be symbolically linked here.
      'paths.prefix'   is the path where all recipes will be installed to.
            Each recipe lives in its own silo. If you installed 'ag' with
            the above config it would reside in '/tmp/pakit/builds/ag' .
      'paths.source'   is where all source code will be downloaded and built.
      'log.enabled'    toggle file logging.
      'log.file'       where to find the log.
      'defaults'       a dictionary of values to provide to all recipes.
      'defaults.repo'  by convention, the name of a repository in Recipe.repos.
            Will be used to download the source code for all recipes.
            By convention, 'stable' will fetch the latest tagged release and
            'unstable' will fetch from the latest commit.
      'ag'             a dictionary of values, will be merged with 'defaults'.
            Anything in 'ag' will override 'defaults'.

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

    def __contains__(self, key):
        return key in self.__conf

    def get(self, key):
        """
        Get the value of a key at some position in the config dictionary.

        Args:
            key: A period separated path down the config dictionary.
                For example `paths.prefix`, would be equivalent
                to conf['paths']['prefix']

        Returns:
            The object stored at *key*.

        Raises:
            KeyError: The key didn't exist.
        """
        obj = self.__conf
        leaf = key.split('.')[-1]
        for word in key.split('.')[0:-1]:
            obj = obj.get(word, None)
        return obj[leaf]

    def get_opts(self, recipe_name):
        """
        Retrieves from config all options needed for recipe_name.

        Args:
            recipe_name: The recipe to look for.

        Returns:
            A dictionary that starts with everything under conf['default'] and
            updates the dictionary with the values in:
                - conf['paths']
                - conf[recipe_name]
        """
        opts = copy.deepcopy(self.get('defaults'))
        opts.update(self.get('paths'))
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

    def set(self, key, val):
        """
        Modify the underlying config, will create nodes if needed.

        Args:
            key: A period separated path down the config dictionary.
                For example `paths.prefix`, would be equivalent
                to conf['paths']['prefix'].
            val: The value to assign to the key.
        """
        obj = self.__conf
        leaf = key.split('.')[-1]
        for word in key.split('.')[0:-1]:
            new_obj = obj.get(word, None)
            if new_obj is None:
                obj[word] = dict()
                new_obj = obj.get(word)
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


class InstallDB(YamlMixin, object):
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
