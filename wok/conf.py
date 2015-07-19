""" Config reader & writer. Depends on PyYAML. """
from __future__ import absolute_import

import copy
import json
import logging
import os
import yaml

# The default file
TEMPLATE = {
    'paths': {
        'prefix': '/tmp/wok/builds',
        'link': '/tmp/wok/links',
        'source': '/tmp/wok/src',
    },
    'log': {
        'enabled': True,
        'file': '/tmp/wok/main.log',
    },
}

class Config(object):
    """ All logic to manage configuration parsing. """
    def __init__(self, filename=os.path.expanduser('~/.wok.yaml')):
        self.__conf = copy.deepcopy(TEMPLATE)
        self.__filename = filename

    def __str__(self):
        pretty_js = json.dumps(self.__conf, sort_keys=True, indent=2)
        return 'Config File: {fname}\nContents: \n{jso}'.format(
                name=self.filename, jso=pretty_js)

    def __getattr__(self, name):
        return self.__conf.get(name, None)

    def __getitem__(self, name):
        return self.__conf.get(name, None)

    @property
    def filename(self):
        """ The filename of the yaml config. """
        return self.__filename

    @filename.setter
    def filename(self, new_filename):
        if not os.path.exists(new_filename):
            logging.error('File not found: {0}'.format(new_filename))

        self.__filename = new_filename

    def read(self):
        """ Load associated config file. """
        try:
            with open(self.__filename) as fin:
                self.__conf = yaml.load(fin)
            logging.debug('Config Loaded: %s', self)
        except IOError as exc:
            logging.error('Failed to load user config. %s', exc)

    def reset(self):
        """ Reset to default template. """
        self.__conf = copy.deepcopy(TEMPLATE)

    def set(self, name, val):
        """ Modify underlying config, will create nodes if needed.

            name: some path down the dict, i.e. paths.prefix or logging.enable
        """
        obj = self.__conf
        leaf = name.split('.')[-1]
        for word in name.split('.')[0:-1]:
            new_obj = obj.get(word, None)
            if new_obj is None:
                obj[word] = dict()
                new_obj = obj.get(word)
            obj = new_obj
        obj[leaf] = val

    def write(self):
        """ Allows to write the values to a file. """
        with open(self.__filename, 'w') as fout:
            yaml.dump(self.__conf, fout, default_flow_style=False)
            logging.debug('Config written to: %s', self.__filename)
