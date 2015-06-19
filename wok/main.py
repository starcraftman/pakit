#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import

import argparse
import logging
import os
import shutil

from formula import Ag
from wok.conf import Config

# TODO: Path modification during operation by os.environ
def main():
    # TODO: Add choices kwarg for install/remove based on avail formula
    mesg = """wok is a homebrew like installer.

    Available Programs:
    """
    parser = argparse.ArgumentParser(description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument('-w', '--wokinit',
                        default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    mut1 = parser.add_mutually_exclusive_group()
    mut1.add_argument('-i', '--install', nargs='+',
                        metavar='PROG', help='install specified programs')
    mut1.add_argument('-r', '--remove', nargs='+',
                        metavar='PROG', help='remove specified programs')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                        help='update installed programs')
    args = parser.parse_args()

    config = Config(args.wokinit)
    build_dir = config.install_to

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    logging.debug('CLI: %s', args)
    logging.debug('Wok Config: %s', config)

    if args.install is not None and 'ag' in args.install:
        install_dir = os.path.join(config.install_to, Ag.__name__.lower())
        build = Ag(install_dir)
        build.download()
        build.build()
        assert build.verify()

if __name__ == '__main__':
    main()
