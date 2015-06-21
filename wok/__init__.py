""" Wok
    Implements a homebrew like program.
"""
from __future__ import absolute_import

import os
import logging
import logging.handlers

from wok.recipe import Recipe

__version__ = 0.1

# TODO: Switch to rotating FileHandler later
def init_logging(log_file='/tmp/wok/main.log'):
    """ Setup project wide file logging. """
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
    log_datefmt = '[%d/%m %H%M.%S]'
    logging.basicConfig(filename=log_file, level=logging.DEBUG,
            format=log_fmt, datefmt=log_datefmt)

    root = logging.getLogger()
    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)
    stream_fmt = logging.Formatter(fmt=log_fmt, datefmt=log_datefmt)
    stream.setFormatter(stream_fmt)
    root.addHandler(stream)

init_logging()
