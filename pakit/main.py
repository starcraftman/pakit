"""
The main entry point for pakit.

Acts as an intermediary between program arguments and pakit Tasks.
"""
from __future__ import absolute_import, print_function

import argparse
import glob
import logging
import logging.handlers
import os
import sys
import traceback

from pakit import __version__
from pakit.conf import Config, InstallDB
from pakit.exc import PakitError, PakitDBError
from pakit.graph import DiGraph, topological_sort
from pakit.recipe import RecipeDB
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, ListInstalled, ListAvailable,
    DisplayTask, RelinkRecipes, SearchTask
)
import pakit.conf
import pakit.shell


PLOG = logging.getLogger('pakit').info


def create_args_parser():
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
        Run in shell: `{1} --create-conf`
            This writes the default config to $HOME/.pakit.yml

        Run in shell: `export PATH=/tmp/pakit/links/bin:$PATH`
            This is where all program bins will link to by default.

    For project development or to report bugs:
        https://github.com/starcraftman/pakit

    Additional Information:
        - Man pages, `man pakit` or `man pakit_recipes`
        - `pydoc pakit`
        - See DEMO.md inside pakit site package.

    Recipes:
        pakit_recipes/ag.py is an example recipe.
        User made recipes can be put in $HOME/.pakit/recipes by default.
        If two recipes have same name, last one in will be executed.
    """.format(prog_name.capitalize(), prog_name)
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
    parser.add_argument('-c', '--conf', help='yaml config file')
    parser.add_argument('--create-conf', default=False, action='store_true',
                        help='write the default config to CONF')
    parser.add_argument('-d', '--display', nargs='+', metavar='RECIPE',
                        help='show detailed information about RECIPE(s)')
    mut1.add_argument('-i', '--install', nargs='+',
                      metavar='RECIPE', help='install specified RECIPE(s)')
    mut1.add_argument('-k', '--search', nargs='+', metavar='WORD',
                      help='search names & descriptions for WORD')
    parser.add_argument('-l', '--list', default=False,
                        action='store_true', help='list installed recipes')
    parser.add_argument('--list-short', default=False, action='store_true',
                        help='list installed recipes, terse output')
    parser.add_argument('--relink', default=False, action='store_true',
                        help='relink installed recipes')
    mut1.add_argument('-r', '--remove', nargs='+',
                      metavar='RECIPE', help='remove specified RECIPE(s)')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                      help='update all installed recipes')

    return parser


def environment_check(config):
    """
    Check the environment is correct.

    Guarantee built programs always first in $PATH for Commands.
    """
    bin_dir = os.path.join(config.get('pakit.paths.link'), 'bin')
    if os.environ['PATH'].find(bin_dir) == -1:
        PLOG('To use built recipes %s must be on shell $PATH.', bin_dir)
        PLOG('  For Most Shells: export PATH=%s:$PATH', bin_dir)
    os.environ['PATH'] = bin_dir + ':' + os.environ['PATH']


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
    config = Config(config_file)
    pakit.conf.CONFIG = config
    log_init(config)
    logging.debug('Global Config: %s', config)

    for path in config.get('pakit.paths').values():
        try:
            os.makedirs(path)
        except OSError:
            pass

    prefix = config.get('pakit.paths.prefix')
    pakit.conf.IDB = InstallDB(os.path.join(prefix, 'installed.yml'))
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

    link_man_pages(config.get('pakit.paths.link'))
    environment_check(config)

    return config


def link_man_pages(link_dir):
    """
    Silently links project man pages into link dir.
    """
    src = os.path.join(os.path.dirname(__file__), 'extra')
    dst = os.path.join(link_dir, 'share', 'man', 'man1')
    try:
        os.makedirs(dst)
    except OSError:
        pass

    man_pages = [os.path.basename(fname) for fname in
                 glob.glob(os.path.join(src, '*.1'))]
    for page in man_pages:
        try:
            s_man, d_man = os.path.join(src, page), os.path.join(dst, page)
            os.symlink(s_man, d_man)
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

    while len(root.handlers):
        root.removeHandler(root.handlers[0])

    rot = logging.handlers.RotatingFileHandler(log_file,
                                               mode='a',
                                               maxBytes=2 ** 22,
                                               backupCount=4)
    rot.setLevel(logging.DEBUG)
    rot.setFormatter(my_fmt)
    root.addHandler(rot)

    stream = logging.StreamHandler()
    stream.setLevel(logging.ERROR)
    stream.setFormatter(my_fmt)
    root.addHandler(stream)

    # Logger for informing user
    pak = logging.getLogger('pakit')
    while len(pak.handlers):
        pak.removeHandler(pak.handlers[0])

    pak.setLevel(logging.INFO)
    pak_fmt = 'pakit %(asctime)s %(message)s'
    pak_info = logging.Formatter(fmt=pak_fmt, datefmt='[%H:%M:%S]')
    pak_stream = logging.StreamHandler()
    pak_stream.setFormatter(pak_info)
    pak.addHandler(pak_stream)


def add_deps_for(recipe_name, graph):
    """
    Recursively add a recipe_name and all reqirements to the graph.

    NOTE: Cycles may be present in the graph when recursion terminates.
    Even so, this function will NOT recurse endlessly.

    Args:
        graph: A directed graph.
        recipe_name: A recipe in RecipeDB.

    Raises:
        PakitDBError: No matching recipe in RecipeDB.
        CycleInGraphError: A cycle was detected in the recursion.
    """
    if recipe_name in graph:
        return

    recipe = RecipeDB().get(recipe_name)
    graph.add_vertex(recipe_name)

    requires = getattr(recipe, 'requires', [])
    graph.add_edges(recipe_name, requires)
    for requirement in requires:
        add_deps_for(requirement, graph)


def order_tasks(recipe_names, task_class):
    """
    Order the recipes so that all dependencies can be met.

    Args:
        recipe_names: List of recipe names.
        task_class: The Task to be carried out on the recipes.

    Returns:
        A list of task_class instances ordered to meet dependencies.

    Raises:
        CycleInGraphError: The dependencies could not be resolved
        as there was a cycle in the dependency graph.
    """
    graph = DiGraph()

    for recipe_name in recipe_names:
        add_deps_for(recipe_name, graph)

    return [task_class(recipe_name) for recipe_name in topological_sort(graph)]


def parse_tasks_display(args):
    """
    Parse args for DisplayTasks.
    """
    if args.display:
        return [DisplayTask(prog) for prog in args.display]
    else:
        return []


def parse_tasks_install(args):
    """
    Parse args for InstallTask(s).
    """
    if args.install:
        return order_tasks(args.install, InstallTask)
    else:
        return []


def parse_tasks_list_available(args):
    """
    Parse args for  ListAvailable task.
    """
    if args.available or args.available_short:
        return [ListAvailable(args.available_short)]
    else:
        return []


def parse_tasks_list_installed(args):
    """
    Parse args for ListInstalled task.
    """
    if args.list or args.list_short:
        return [ListInstalled(args.list_short)]
    else:
        return []


def parse_tasks_relink(args):
    """
    Parse args for RelinkRecipes task.
    """
    if args.relink:
        return [RelinkRecipes()]
    else:
        return []


def parse_tasks_remove(args):
    """
    Parse args for RemoveTask(s).
    """
    if args.remove:
        return [RemoveTask(recipe) for recipe in args.remove]
    else:
        return []


def parse_tasks_search(args):
    """
    Parse args for DisplayTask(s).
    """
    if args.search:
        return [SearchTask(RecipeDB().names(desc=True), args.search)]
    else:
        return []


def parse_tasks_update(args):
    """
    Parse args for UpdateTask(s).
    """
    if args.update:
        recipes_to_update = [recipe for recipe, _ in pakit.conf.IDB]
        return order_tasks(recipes_to_update, UpdateTask)
    else:
        return []


def parse_tasks(args):
    """
    Parse the program arguments into a list of Tasks to execute

    Args:
        args: An argparse object to map onto tasks.

    Returns:
        A list of Tasks.
    """
    tasks = []

    cur_module = sys.modules[__name__]
    parsers = [getattr(cur_module, fname) for fname in dir(cur_module)
               if fname.find('parse_tasks_') == 0]
    for parser in parsers:
        tasks.extend(parser(args))

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


def main(argv=None):
    """
    The main entry point for this program.

    Args:
        argv: A list of program options, if None use sys.argv.
    """
    if argv is None:
        argv = sys.argv

    parser = create_args_parser()
    if len(argv) == 1:
        logging.error('No arguments. What should I do?')
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args(argv[1:])
    if not args.conf:
        args.conf = search_for_config(os.path.expanduser('~/.pakit.yml'))
    if args.create_conf:
        write_config(args.conf)

    config = global_init(args.conf)
    logging.debug('CLI: %s', args)
    PLOG('Loading config from: ' + config.filename)

    try:
        tasks = parse_tasks(args)
        for task in tasks:
            PLOG('Running: %s', str(task))
            task.run()

        if len(tasks) == 0 and args.update:
            PLOG('Nothing to update.')

    except PakitDBError as exc:
        PLOG(str(exc))
    except PakitError as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()  # pragma: no cover
