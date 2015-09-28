"""
The main entry point for pakit.

Acts as an intermediary between program arguments and pakit Tasks.
"""
from __future__ import absolute_import, print_function

import argparse
import logging
import logging.handlers
import os
import sys
import traceback

from pakit import __version__
from pakit.conf import Config, InstallDB
from pakit.exc import PakitError, PakitDBError
from pakit.recipe import RecipeDB
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, ListInstalled, ListAvailable,
    DisplayTask, SearchTask
)
import pakit.conf
import pakit.shell


PLOG = logging.getLogger('pakit')


def args_parser():
    """
    Create the program argument parser.

    Returns:
        An argparse parser object.
    """
    prog_name = os.path.basename(os.path.dirname(sys.argv[0]))
    mesg = """
    {0} is a build tool providing a package manager like interface
    to build & install recipes into local paths.

    First Time Run:
        Run in shell: `{0} --create-conf`
            This writes the default config to $HOME/.pakit.yml

        Run in shell: `export PATH=/tmp/pakit/links/bin:$PATH`
            This is where all programs eventually linked to by default.
            See man page for more configuration information.

    For project development or to report bugs:
        https://github.com/starcraftman/pakit

    Additional Information:
        - Man page, provided inside `pakit/extra/pakit.1`. It is automatically
        available via `man pakit` if `paths.link` is on your shell $PATH.
        - `pydoc pakit`
        - See DEMO.md inside pakit site package.

    Recipes:
        pakit_recipes/ag.py is an example recipe
        User made recipes can be put in $HOME/.pakit/recipes by default.
        If two recipes have same name, last one in will be executed.
    """.format(prog_name)
    parser = argparse.ArgumentParser(prog=prog_name, description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    mut1 = parser.add_mutually_exclusive_group()
    parser.add_argument('-v', '--version', action='version',
                        version='pakit {0}\nALPHA!'.format(__version__))
    parser.add_argument('-a', '--available', default=False,
                        action='store_true', help='list available recipes')
    parser.add_argument('--available-short', default=False,
                        action='store_true',
                        help='list available recipes, terse output')
    parser.add_argument('-c', '--conf',
                        default=os.path.expanduser('~/.pakit.yml'),
                        help='yaml config file')
    parser.add_argument('--create-conf', default=False, action='store_true',
                        help='write the default config to CONF')
    parser.add_argument('-d', '--display', nargs='+', metavar='PROG',
                        help='show detailed information on recipe')
    mut1.add_argument('-i', '--install', nargs='+',
                      metavar='PROG', help='install specified program(s)')
    mut1.add_argument('-k', '--search', nargs='+', metavar='WORD',
                      help='search names & descriptions for WORD')
    parser.add_argument('-l', '--list', default=False,
                        action='store_true', help='list installed programs')
    parser.add_argument('--list-short', default=False, action='store_true',
                        help='list installed recipes, terse output')
    mut1.add_argument('-r', '--remove', nargs='+',
                      metavar='PROG', help='remove specified program(s)')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                      help='update installed programs')

    return parser


def global_init(config_file):
    """
    Performs global configuration of pakit.

    Must be called before using pakit. Will ...
        - Read user configuration.
        - Initialize the logging system.
        - Populate the recipe database.
        - Create configured folders.
        - Setup pakit man page.

    Args:
        config_file: The YAML configuration filename.

    Returns:
        The loaded config object.
    """
    config = Config(search_for_config(config_file))
    pakit.conf.CONFIG = config
    log_init(config)
    logging.debug('Global Config: %s', config)

    for path in config.get('pakit.paths').values():
        try:
            os.makedirs(path)
        except OSError:
            pass

    prefix = config.get('pakit.paths.prefix')
    pakit.conf.IDB = InstallDB(os.path.join(prefix, 'installed.yaml'))
    logging.debug('InstallDB: %s', pakit.conf.IDB)
    pakit.shell.TMP_DIR = os.path.dirname(prefix)

    recipes = RecipeDB(config)
    default = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'pakit_recipes')
    recipes.index(default)
    try:
        recipes.index(config.get('pakit.paths.recipes'))
    except KeyError:
        pass

    link_man_page(config.get('pakit.paths.link'))

    return config


def link_man_page(link_dir):
    """
    Silently links man page into link dir.
    """
    src = os.path.join(os.path.dirname(__file__), 'extra', 'pakit.1')
    dst = os.path.join(link_dir, 'share', 'man', 'man1', 'pakit.1')
    try:
        os.makedirs(os.path.dirname(dst))
    except OSError:
        pass
    try:
        os.symlink(src, dst)
    except OSError:
        pass


def log_init(config):
    """
    Setup project wide logging.

    Specifically this will setup both file and console logging.
    """
    log_file = config.get('pakit.log.file')
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

    # Logger for informing user
    pak_fmt = 'pakit: %(asctime)s %(message)s'
    pak_info = logging.Formatter(fmt=pak_fmt, datefmt='[%H:%M:%S]')
    stream_i = logging.StreamHandler()
    stream_i.setFormatter(pak_info)
    pak = logging.getLogger('pakit')
    pak.setLevel(logging.INFO)
    pak.addHandler(stream_i)


def parse_tasks(args):
    """
    Parse the program arguments into a list of Tasks to execute

    Args:
        args: An argparse object to map onto tasks.

    Returns:
        A list of Tasks.
    """
    tasks = []

    if args.install:
        tasks.extend([InstallTask(prog) for prog in args.install])
    if args.remove:
        tasks.extend([RemoveTask(prog) for prog in args.remove])
    if args.update:
        tasks.extend([UpdateTask(prog) for prog, _ in pakit.conf.IDB])
    if args.available:
        tasks.append(ListAvailable(False))
    if args.available_short:
        tasks.append(ListAvailable(True))
    if args.display:
        tasks.extend([DisplayTask(prog) for prog in args.display])
    if args.search:
        tasks.append(SearchTask(RecipeDB().names(desc=True), args.search))
    if args.list:
        tasks.append(ListInstalled(False))
    if args.list_short:
        tasks.append(ListInstalled(True))

    return tasks


def search_for_config(default_config=None):
    """
    Search for the most relevant configuration file.

    Will search from current dir upwards until root for config files matching:
        - .pakit.yml
        - .pakit.yaml
        - pakit.yml
        - pakit.yaml

    If nothing found, search in $HOME and then $HOME/.pakit for same files.

    If still nothing found, return default_config.

    Args:
        default_config: The default config if nothing else present.

    Returns:
        If a path existed, return found filename.
        If no paths matched an existing file return the default_config.
    """
    folders = [os.getcwd()]
    cur_dir = os.path.dirname(os.getcwd())
    while cur_dir != '/':
        folders.append(cur_dir)
        cur_dir = os.path.dirname(cur_dir)
    folders.append(os.path.expanduser('~'))
    folders.append(os.path.expanduser('~/.pakit'))

    for folder in folders:
        for conf in ['.pakit.yml', '.pakit.yaml', 'pakit.yml', 'pakit.yaml']:
            config_file = os.path.join(folder, conf)
            if os.path.exists(config_file):
                return config_file

    return default_config


def write_config(config_file):
    """
    Writes the DEFAULT config to the config file.
    Overwrites the file if present.

    Raises:
        PakitError: File exists and is a directory.
        PakitError: File could not be written to.
    """
    config = Config(config_file)
    try:
        os.remove(config.filename)
    except OSError:
        if os.path.isdir(config.filename):
            raise PakitError('Config path is a directory.')
    try:
        config.reset()
        config.write()
        print('pakit: Wrote default config to: ' + config.filename)
    except (IOError, OSError):
        raise PakitError('Failed to write to ' + config.filename)
    finally:
        sys.exit(0)


# TODO: Path modification during operation by os.environ
def main(argv=None):
    """
    The main entry point for this program.

    Args:
        argv: A list of program options, if None use sys.argv.
    """
    if argv is None:
        argv = sys.argv

    parser = args_parser()
    if len(argv) == 1:
        logging.error('No arguments. What should I do?')
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args(argv[1:])
    if args.create_conf:
        write_config(args.conf)

    config = global_init(args.conf)
    logging.debug('CLI: %s', args)
    PLOG.info('Loading config from: ' + config.filename)

    try:
        tasks = parse_tasks(args)
        for task in tasks:
            PLOG.info('Running: %s', str(task))
            task.run()

        if len(tasks) == 0 and args.update:
            PLOG.info('Nothing to update.')

    except PakitDBError as exc:
        PLOG.info(str(exc))
    except PakitError as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()  # pragma: no cover
