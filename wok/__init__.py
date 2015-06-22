""" Wok
    Implements a homebrew like program.
"""
from __future__ import absolute_import

import os
import logging
import logging.handlers

from wok.recipe import Recipe

__version__ = 0.1

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

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    log_fmt = '%(levelname)s %(asctime)s %(threadName)s ' \
            '%(filename)s %(message)s'
    my_fmt = logging.Formatter(fmt=log_fmt, datefmt='[%d/%m %H%M.%S]')

    max_size = (1024 ** 2) * 1
    rot = logging.handlers.RotatingFileHandler(log_file, mode='w',
            maxBytes=max_size, backupCount=4)
    rot.setLevel(logging.DEBUG)
    rot.setFormatter(my_fmt)
    root.addHandler(rot)

    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)
    stream.setFormatter(my_fmt)
    root.addHandler(stream)

init_logging()
