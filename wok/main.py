""" The obligatory main entry point. """
from __future__ import absolute_import, print_function

import argparse
import logging
import logging.handlers
import os
import sys
import traceback

from wok import __version__
from wok.conf import Config, InstallDB
from wok.recipe import RecipeDB
from wok.task import InstallTask, RemoveTask, UpdateTask, ListInstalled, SearchTask
import wok.shell
import wok.task

def parse_tasks(args):
    """ Take program arguments and make a task list. """
    tasks = []

    if args.install is not None:
        tasks.extend([InstallTask(prog) for prog in args.install])
    if args.remove is not None:
        tasks.extend([RemoveTask(prog) for prog in args.remove])
    if args.update is True:
        tasks.extend([UpdateTask(prog) for prog, _ in wok.task.IDB])
    if args.list is True:
        tasks.append(ListInstalled())

    return tasks

def global_init(wok_file):
    """ Do setup of the global environment.

        Returns loaded config.
    """
    config = Config(wok_file)
    init_logging(config.get('log.file'))
    logging.debug('Wok Config: %s', config)

    for dirname in config.get('paths').values():
        try:
            os.makedirs(dirname)
        except OSError:
            pass

    prefix = config.get('paths.prefix')
    wok.shell.TMP_DIR = os.path.dirname(prefix)
    wok.task.Task.set_config(config)
    RecipeDB(config)
    wok.task.IDB = InstallDB(os.path.join(prefix, 'installed.yaml'))

    return config

def init_logging(log_file):
    """ Setup project wide file logging. """
    try:
        os.makedirs(os.path.dirname(log_file))
    except OSError:
        pass

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    log_fmt = '%(levelname)s %(asctime)s %(threadName)s ' \
            '%(filename)s %(message)s'
    my_fmt = logging.Formatter(fmt=log_fmt, datefmt='[%d/%m %H%M.%S]')

    while len(root.handlers) != 0:
        root.removeHandler(root.handlers[0])

    max_size = 1024 ** 2
    rot = logging.handlers.RotatingFileHandler(log_file, mode='a',
            maxBytes=max_size, backupCount=4)
    rot.setLevel(logging.DEBUG)
    rot.setFormatter(my_fmt)
    root.addHandler(rot)

    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)
    stream.setFormatter(my_fmt)
    root.addHandler(stream)

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
    config = global_init(args.conf)
    logging.debug('CLI: %s', args)

    if args.create_conf:
        config.write()

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
        logging.error(traceback.format_exc())

if __name__ == '__main__':
    main()
