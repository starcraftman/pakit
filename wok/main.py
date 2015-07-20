""" The obligatory main entry point. """
from __future__ import absolute_import, print_function

import argparse
import logging
import os
import shutil
import sys

from wok import __version__
from wok.conf import Config
from wok.recipe import RecipeDB
from wok.task import *

def parse_tasks(args):
    """ Take program arguments and make a task list. """
    tasks = []

    if args.install is not None:
        tasks.extend([InstallTask(prog) for prog in args.install])
    if args.remove is not None:
        tasks.extend([RemoveTask(prog) for prog in args.remove])
    if args.update is True:
        pass
    if args.list is True:
        tasks.append(ListInstalled())

    return tasks


def dir_check(paths):
    for dirname in [paths.get('prefix'), paths.get('link'), paths.get('source')]:
        try:
            os.makedirs(dirname)
        except OSError:
            pass

# TODO: Path modification during operation by os.environ
def main():
    # TODO: Add choices kwarg for install/remove based on avail formula
    mesg = """    wok is a homebrew like installer"""
    parser = argparse.ArgumentParser(description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
                        version='wok {0}\nALPHA SOFTWARE!'.format(__version__))
    parser.add_argument('-c', '--conf', default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    parser.add_argument('--create-conf', default=False, action='store_true',
                        help='(over)write the conf at $HOME/.wok.yaml')
    mut1 = parser.add_mutually_exclusive_group()
    mut1.add_argument('-i', '--install', nargs='+',
                        metavar='PROG', help='install specified program(s)')
    mut1.add_argument('-r', '--remove', nargs='+',
                        metavar='PROG', help='remove specified program(s)')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                        help='update installed programs')
    mut1.add_argument('-l', '--list', default=False, action='store_true',
                        help='list installed programs')

    # Require at least one for now.
    if len(sys.argv) == 1:
        parser.print_usage()
        logging.error('No arguments. What should I do?')
        sys.exit(1)

    args = parser.parse_args()
    logging.debug('CLI: %s', args)

    config = Config(args.conf)
    config.read()
    logging.debug('Wok Config: %s', config)

    if args.create_conf:
        config.write()

    dir_check(config.paths)
    Task.set_config(config)
    RecipeDB(config)

    try:
        tasks = parse_tasks(args)
        if len(tasks) == 0:
            parser.print_usage()
            logging.error('Insufficient arguments. What should I do?')
            sys.exit(1)

        for task in tasks:
            task.do()
    except Exception as exc:
        logging.error(exc)

if __name__ == '__main__':
    main()
