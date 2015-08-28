""" Config reader & writer. Depends on PyYAML. """
from __future__ import absolute_import

import copy
import json
import logging
import os
import time
import yaml

# The default global config, to start users off right
TEMPLATE = {
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
}


class YamlMixin(object):
    """ Provides YAML file interface for read/write configs. """
    def __init__(self, filename):
        super(YamlMixin, self).__init__()
        self.__filename = filename

    @property
    def filename(self):
        """ The filename to read/write. """
        return self.__filename

    @filename.setter
    def filename(self, new_filename):
        """ Set the filename. """
        if not os.path.exists(new_filename):
            logging.error('File not found: %s', new_filename)
        self.__filename = new_filename

    def read_from(self):
        """ Loads the config file and returns the object created. """
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
        """ Write the object to the config file. """
        with open(self.filename, 'w') as fout:
            yaml.dump(obj, fout, default_flow_style=False)
            logging.debug('Config written to: %s', self.filename)


class Config(YamlMixin, object):
    """ All logic to manage configuration parsing. """
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

    def get(self, key):
        """ Allow simple specification of path to value down tree.

            key: a path down tree like `node.node2.leaf`,
            where node & node2 are dicts & leaf is the key to node2.
        """
        obj = self.__conf
        leaf = key.split('.')[-1]
        for word in key.split('.')[0:-1]:
            obj = obj.get(word, None)
        return obj[leaf]

    def get_opts(self, name):
        """ Overide defaults with specific opts if set. """
        opts = copy.deepcopy(self.get('defaults'))
        opts.update(self.get('paths'))
        try:
            opts.update(self.get(name))
        except KeyError:
            pass
        return opts

    def reset(self):
        """ Reset to default template. """
        self.__conf = copy.deepcopy(TEMPLATE)

    def set(self, key, val):
        """ Modify underlying config, will create nodes if needed.

            key: See get, same specification.
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
        """ Read from the config file. """
        self.__conf = self.read_from()

    def write(self):
        """ Write to the config file. """
        self.write_to(self.__conf)


class InstallDB(YamlMixin, object):
    """ Stores all information on what IS actually installed. """
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

    def get(self, prog):
        """ Return the associated entry or None. """
        return self.__conf.get(prog, None)

    def set(self, key, value):
        """ Allow bypass recipe add. """
        self.__conf[key] = value

    def add(self, recipe):
        """ Call with program name & opts to put into yaml config. """
        time_s = time.time()
        self.__conf[recipe.name] = {
            'date': time.strftime('%H:%M:%S %d/%m/%y', time.localtime(time_s)),
            'hash': recipe.repo.cur_hash,
            'repo': recipe.repo_name,
            'timestamp': time_s,
        }
        self.write()

    def remove(self, prog):
        """ Remove an entry. """
        del self.__conf[prog]
        self.write()

    def read(self):
        """ Read from the config file. """
        self.__conf = self.read_from()

    def write(self):
        """ Write to the config file. """
        self.write_to(self.__conf)
