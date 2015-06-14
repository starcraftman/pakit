""" Wok
    Implements a homebrew like program.
"""
from __future__ import absolute_import

import os
import logging
import logging.handlers

from wok.recipe import Recipe

__version__ = 0.1

# Setup project wide file logging
LOG_FILE = '/tmp/wok/main.log'
try:
    os.makedirs(os.path.dirname(LOG_FILE))
except OSError:
    pass
try:
    os.remove(LOG_FILE)
except OSError:
    pass

FORMAT = '%(levelname)s %(asctime)s %(threadName)s %(filename)s %(message)s'
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG,
        format=FORMAT, datefmt='[%d/%m/%y %H%M.%S]')
logging.debug('Module init finished.')
