#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function

import argparse
import logging
import os
import shutil
import yaml
try:
    from yaml import CLoader as Loader
    print("USING CLOADER")
except ImportError:
    from yaml import Loader

from formula import Ag

BUILD_DIR = '/tmp/wok/builds'

def load_config(wok_file):
    with open(wok_file) as input:
        return yaml.load(input)

def main():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    # TODO: Add choices kwarg for install/remove based on avail formula
    mesg = """wok is a homebrew like installer."""
    parser = argparse.ArgumentParser(description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--conf', nargs='?',
                        default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    ex_main = parser.add_mutually_exclusive_group()
    ex_main.add_argument('-i', '--install', nargs='*',
                        metavar='PROG', help='install specified programs')
    ex_main.add_argument('-r', '--remove', nargs='*',
                        metavar='PROG', help='remove specified programs')
    ex_main.add_argument('-u', '--update', default=False, action='store_true',
                        help='update installed programs')
    args = parser.parse_args()
    logging.debug('CLI ARGS: %s', args)

    #install_dir = os.path.join(BUILD_DIR, Ag.__name__.lower())
    #build = Ag(install_dir)
    #build.download()
    #build.build()
    #assert build.verify()

if __name__ == '__main__':
    main()
