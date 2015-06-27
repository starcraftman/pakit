""" Config reader & writer. Depends on PyYAML. """
from __future__ import absolute_import

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
    def __init__(self, filename):
        self.__conf = TEMPLATE
        self.__filename = filename
        self.load()

    def __str__(self):
        return str(self.__conf)

    def __getattr__(self, name):
        return self.__conf.get(name, None)

    def __getitem__(self, name):
        return self.__conf.get(name, None)

    def set(self, name, val):
        self.__conf[name] = val

    def load(self, filename=None):
        """ If it can't load file, print error and use default. """
        if filename is not None:
            self.__filename = filename

        try:
            with open(self.__filename) as fin:
                self.__conf = yaml.load(fin)
            logging.debug('Config Loaded: %s', self)
        except IOError as exc:
            logging.error('Failed to load user config. %s', exc)

    def write(self, **kwargs):
        """ Allows to write the values to a file. """
        new_name = kwargs.get('filename', None)
        if new_name is not None:
            self.__filename = new_name

        if kwargs.get('default', False):
            self.__conf = TEMPLATE

        with open(self.__filename, 'w') as fout:
            yaml.dump(self.__conf, fout, default_flow_style=False)
            logging.debug('Config written to: %s', self.__filename)
