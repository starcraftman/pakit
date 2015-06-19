#!/usr/bin/env python
# encoding: utf-8

""" Config reader & writer. Depends on PyYAML. """
from __future__ import absolute_import, print_function

import logging
import yaml

# The default file
TEMPLATE = {
    'install_to'  : '/tmp/wok/builds',
    'link_to'     : '/tmp/wok/links',
    'log_file'    : '/tmp/wok/main.log',
    'log_on'      : True,
}

class Config(object):
    def __init__(self, filename):
        self._conf = TEMPLATE
        self._filename = filename
        self.load()

    def __str__(self):
        return str(self._conf)

    def __getattr__(self, name):
        return self._conf.get(name, None)

    def set(self, name, val):
        self._conf[name] = val

    def load(self, filename=None):
        if filename is not None:
            self._filename = filename

        try:
            with open(self._filename) as fin:
                self._conf = yaml.load(fin)
            logging.debug('Config Loaded: %s', self)
        except IOError as exc:
            logging.error('Failed to load user config. %s', exc)

    def write(self, filename=None):
        if filename is not None:
            self._filename = filename

        with open(self._filename, 'w') as fout:
            yaml.dump(self._conf, fout, default_flow_style=False)
            logging.debug('Config written to: %s', filename)
