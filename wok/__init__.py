""" Wok
    Implements a homebrew like program.
"""
from __future__ import absolute_import

import os
import logging
import logging.handlers

from wok.recipe import Recipe

__version__ = 0.1

def init_logging():
    """ Setup project wide file logging. """
    log_file = '/tmp/wok/main.log'
    try:
        os.makedirs(os.path.dirname(log_file))
    except OSError:
        pass
    try:
        os.remove(log_file)
    except OSError:
        pass

    log_fmt = '%(levelname)s %(asctime)s %(threadName)s ' \
            '%(filename)s %(message)s'
    logging.basicConfig(filename=log_file, level=logging.DEBUG,
            format=log_fmt, datefmt='[%d/%m %H%M.%S]')

    # TODO: Switch to rotating FileHandler later

init_logging()
