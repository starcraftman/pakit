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
    parser.add_argument('-w', '--wokinit', nargs='?',
                        default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    ex_main = parser.add_mutually_exclusive_group()
    ex_main.add_argument('-i', '--install', dest='action', action='store_const',
                        const='i', help='install specified programs')
    ex_main.add_argument('-r', '--remove', dest='action', action='store_const',
                        const='r', help='remove specified programs')
    ex_main.add_argument('-u', '--update', dest='action', action='store_const',
                        const='u', help='update installed programs')
    parser.add_argument(dest='progs', metavar='PROG', nargs='*',
                        help='programs to install')
    args = parser.parse_args()

    config = Config(args.wokinit)
    build_dir = config.install_to

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    logging.debug('CLI: %s', args)
    logging.debug('Wok Config: %s', config)

    if args.progs is not None and 'ag' in args.progs:
        install_dir = os.path.join(config.install_to, Ag.__name__.lower())
        build = Ag(install_dir)
        build.download()
        build.build()
        assert build.verify()

if __name__ == '__main__':
    main()
