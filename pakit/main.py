""" The obligatory main entry point. """
from __future__ import absolute_import, print_function

import argparse
import logging
import logging.handlers
import os
import sys
import traceback

from pakit import __version__
from pakit.conf import Config, InstallDB
from pakit.recipe import RecipeDB
from pakit.task import (InstallTask, RemoveTask, UpdateTask, ListInstalled,
                        ListAvailable, DisplayTask, SearchTask)
import pakit.shell
import pakit.task


def parse_tasks(args):
    """ Take program arguments and make a task list. """
    tasks = []

    if args.install:
        tasks.extend([InstallTask(prog) for prog in args.install])
    if args.remove:
        tasks.extend([RemoveTask(prog) for prog in args.remove])
    if args.update:
        tasks.extend([UpdateTask(prog) for prog, _ in pakit.task.IDB])
    if args.available:
        tasks.append(ListAvailable())
    if args.display:
        tasks.extend([DisplayTask(prog) for prog in args.display])
    if args.search:
        tasks.append(SearchTask(RecipeDB().names(desc=True), args.search))
    if args.list:
        tasks.append(ListInstalled())

    return tasks


def global_init(pakit_file):
    """ Do setup of the global environment.

        Returns loaded config.
    """
    config = Config(pakit_file)
    init_logging(config.get('log.file'))
    logging.debug('Pakit Config: %s', config)

    for path in config.get('paths').values():
        try:
            os.makedirs(path)
        except OSError:
            pass

    prefix = config.get('paths.prefix')
    pakit.shell.TMP_DIR = os.path.dirname(prefix)
    pakit.task.Task.set_config(config)

    recipes = RecipeDB(config)
    default = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'formula')
    user_recipes = config.get('paths').get('recipes',
                                           os.path.expanduser('~/.pakit'))
    for path in [default, user_recipes]:
        recipes.update_db(path)
    pakit.task.IDB = InstallDB(os.path.join(prefix, 'installed.yaml'))

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
                                               maxBytes=max_size,
                                               backupCount=4)
    rot.setLevel(logging.DEBUG)
    rot.setFormatter(my_fmt)
    root.addHandler(rot)

    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)
    stream.setFormatter(my_fmt)
    root.addHandler(stream)


def args_parser():
    """ The arguments parser, it is fairly large. """
    prog_name = os.path.basename(os.path.dirname(sys.argv[0]))
    mesg = """
    {0} is a meta build tool providing a package manager like interface
    to build & install recipes into local paths.

    Alpha Notes:
        `{0} --create-conf` will create the default config in $HOME/.pakit.yaml

        DESIGN.md explains the config options & recipe format

        formula/ag.py is an example recipe

        User recipes can be stored at $HOME/.pakit
    """.format(prog_name)
    parser = argparse.ArgumentParser(prog=prog_name, description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    mut1 = parser.add_mutually_exclusive_group()
    parser.add_argument('-v', '--version', action='version',
                        version='pakit {0}\nALPHA!'.format(__version__))
    parser.add_argument('-a', '--available', default=False,
                        action='store_true', help='list available recipes')
    parser.add_argument('-c', '--conf',
                        default=os.path.expanduser('~/.pakit.yaml'),
                        help='yaml config file')
    parser.add_argument('--create-conf', default=False, action='store_true',
                        help='(over)write the config to CONF')
    parser.add_argument('-d', '--display', nargs='+', metavar='PROG',
                        help='show detailed information on recipe')
    mut1.add_argument('-i', '--install', nargs='+',
                      metavar='PROG', help='install specified program(s)')
    mut1.add_argument('-k', '--search', nargs='+', metavar='WORD',
                      help='search names & descriptions for WORD')
    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help='list installed programs')
    mut1.add_argument('-r', '--remove', nargs='+',
                      metavar='PROG', help='remove specified program(s)')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                      help='update installed programs')

    return parser


# TODO: Path modification during operation by os.environ
def main(argv=None):
    """ The main entry point. For testing, accepts a dummy argv. """
    if argv is None:
        argv = sys.argv

    # TODO: Add choices kwarg for install/remove based on avail formula
    # Require at least one for now.
    parser = args_parser()
    if len(argv) == 1:
        logging.error('No arguments. What should I do?')
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args(argv[1:])
    config = global_init(args.conf)
    logging.debug('CLI: %s', args)

    if args.create_conf:
        config.write()
        msg = 'Wrote config to: ' + args.conf
        logging.debug(msg)
        print(msg)
        sys.exit(0)

    try:
        tasks = parse_tasks(args)
        if len(tasks) == 0:
            logging.error('No tasks found. Check invocation.')
            parser.print_usage()
            sys.exit(1)

        for task in tasks:
            task.run()
    except Exception as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()  # pragma: no cover
