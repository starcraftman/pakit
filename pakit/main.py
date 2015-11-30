"""
The main entry point for pakit.

Acts as an intermediary between program arguments and pakit Tasks.
"""
from __future__ import absolute_import, print_function

import argparse
from argparse import RawDescriptionHelpFormatter as RawDescriptionHelp
import logging
import logging.handlers
import os
import sys
import traceback

import pakit.conf
import pakit.recipe
import pakit.shell
from pakit import __version__
from pakit.conf import Config, InstallDB
from pakit.exc import PakitError, PakitDBError
from pakit.graph import DiGraph, topological_sort
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, ListInstalled, ListAvailable,
    DisplayTask, RelinkRecipes, SearchTask, CreateConfig, PurgeTask
)


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
        man pakit
        man pakit_recipes
        pydoc pakit

    Recipes:
        User made recipes can be put in $HOME/.pakit/recipes by default.
        If two recipes have same name, last one in will be executed.
        Example recipes can be found in the `pakit_recipes` module.
        A good example is `pakit_recipes/ag.py`.
    """.format(prog_name.capitalize(), prog_name)
    mesg = mesg[0:-5]
    parser = argparse.ArgumentParser(prog=prog_name, description=mesg,
                                     formatter_class=RawDescriptionHelp)
    parser.add_argument('-v', '--version', action='version',
                        version='pakit {0}\nALPHA!'.format(__version__))
    parser.add_argument('-c', '--conf', help='the yaml config file to use')
    subs = parser.add_subparsers(title='subcommands',
                                 description='For additional help: '
                                 'pakit <subcommand> -h')

    sub = subs.add_parser('install',
                          description='Install specified RECIPE(s).')
    sub.add_argument('recipes', nargs='+', metavar='RECIPE',
                     help='one or more RECIPE(s) to install')
    sub.set_defaults(func=parse_install)

    sub = subs.add_parser('remove', description='Remove specified RECIPE(s).')
    sub.add_argument('recipes', nargs='+', metavar='RECIPE',
                     help='one or more RECIPE(s) to remove')
    sub.set_defaults(func=parse_remove)

    sub = subs.add_parser('update',
                          description='Update all recipes installed. '
                          'Alternatively, just specified RECIPE(s)')
    sub.add_argument('recipes', nargs='*', default=(), metavar='RECIPE',
                     help='zero or more RECIPE(s) to update')
    sub.set_defaults(func=parse_update)

    sub = subs.add_parser('list',
                          description='List currently installed recipe(s).')
    sub.add_argument('--short', default=False, action='store_true',
                     help='terse output format')
    sub.set_defaults(func=parse_list)

    sub = subs.add_parser('available',
                          description='List recipes available to install.')
    sub.add_argument('--short', default=False, action='store_true',
                     help='terse output format')
    sub.set_defaults(func=parse_available)

    sub = subs.add_parser('display',
                          description='Information about selected RECIPE(s).')
    sub.add_argument('recipes', nargs='+', metavar='RECIPE',
                     help='display information for one or more RECIPE(s)')
    sub.set_defaults(func=parse_display)

    desc = """Search for WORD(s) in the recipe database.
    The matches for each WORD will be ORed together.

    Default options:
    - Substring match
    - Case insensitive
    - Matches against recipe name or description"""
    sub = subs.add_parser('search', description=desc,
                          formatter_class=RawDescriptionHelp)
    sub.add_argument('words', nargs='+', metavar='WORD',
                     help='search names & descriptions for WORD')
    sub.add_argument('--case', default=False, action='store_true',
                     help='enable case sensitivity, default off')
    sub.add_argument('--names', default=False, action='store_true',
                     help='only search against recipe name,'
                     ' default name and description')
    sub.set_defaults(func=parse_search)

    sub = subs.add_parser('relink',
                          description='Relink all installed RECIPE(s).'
                          '\nAlternatively, relink specified RECIPE(s).',
                          formatter_class=RawDescriptionHelp)
    sub.add_argument('recipes', nargs='*', metavar='RECIPE',
                     help='the RECIPE(s) to manage')
    sub.set_defaults(func=parse_relink)

    sub = subs.add_parser('create-conf',
                          description='(Over)write the selected pakit config.')
    sub.set_defaults(func=parse_create_conf)

    desc = """Remove most traces of pakit. No undo!

    Will delete ...
    - all links from the link directory to pakit's programs.
    - all programs pakit built, including the source trees.
    - all downloaded recipes.
    - all logs and configs EXCEPT the pakit.yml file."""
    sub = subs.add_parser('purge', description=desc,
                          formatter_class=RawDescriptionHelp)
    sub.set_defaults(func=parse_purge)

    return parser


def environment_check(config):
    """
    Check the environment is correct.

    Guarantee built programs always first in $PATH for Commands.
    """
    bin_dir = os.path.join(config.path_to('link'), 'bin')
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
    PLOG('Loaded config from: ' + config.filename)

    for path in config.get('pakit.paths').values():
        try:
            os.makedirs(path)
        except OSError:
            pass

    prefix = config.path_to('prefix')
    pakit.conf.IDB = InstallDB(os.path.join(prefix, 'idb.yml'))
    logging.debug('InstallDB: %s', pakit.conf.IDB)

    manager = pakit.recipe.RecipeManager(config)
    manager.check_for_deletions()
    manager.check_for_updates()
    manager.init_new_uris()
    recipe_db = pakit.recipe.RecipeDB(config)
    for path in manager.paths:
        recipe_db.index(path)
    pakit.recipe.RDB = recipe_db

    pakit.shell.link_man_pages(config.path_to('link'))
    environment_check(config)

    return config


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

    recipe = pakit.recipe.RDB.get(recipe_name)
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


def parse_install(args):
    """
    Parse args for InstallTask(s).
    """
    return order_tasks(args.recipes, InstallTask)


def parse_remove(args):
    """
    Parse args for RemoveTask(s).
    """
    return [RemoveTask(recipe) for recipe in args.recipes]


def parse_update(args):
    """
    Parse args for UpdateTask(s).
    """
    tasks = None
    if len(args.recipes) == 0:
        to_update = [recipe for recipe, _ in pakit.conf.IDB]
        tasks = order_tasks(to_update, UpdateTask)
    else:
        to_update = [recipe for recipe in args.recipes
                     if recipe in pakit.conf.IDB]
        not_installed = sorted(set(args.recipes).difference(to_update))
        if len(not_installed):
            PLOG('Recipe(s) not installed: ' + ', '.join(not_installed))
        tasks = order_tasks(to_update, UpdateTask)

    if len(tasks) == 0:
        PLOG('Nothing to update.')
    return tasks


def parse_display(args):
    """
    Parse args for DisplayTasks.
    """
    return [DisplayTask(prog) for prog in args.recipes]


def parse_available(args):
    """
    Parse args for ListAvailable task.
    """
    return [ListAvailable(args.short)]


def parse_list(args):
    """
    Parse args for ListInstalled task.
    """
    return [ListInstalled(args.short)]


def parse_relink(_):
    """
    Parse args for RelinkRecipes task.
    """
    return [RelinkRecipes()]


def parse_search(args):
    """
    Parse args for DisplayTask(s).
    """
    return [SearchTask(args)]


def parse_create_conf(args):
    """
    Parse args for CreateConfig
    """
    return [CreateConfig(args.conf)]


def parse_purge(_):
    """
    Parse args for PurgeTask
    """
    return [PurgeTask()]


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

    try:
        args = parser.parse_args(argv[1:])
        if not args.conf:
            args.conf = search_for_config(os.path.expanduser('~/.pakit.yml'))

        global_init(args.conf)
        logging.debug('CLI: %s', args)

        for task in args.func(args):
            PLOG('Running: %s', str(task))
            task.run()

    except PakitDBError as exc:
        PLOG(str(exc))
    except PakitError as exc:
        logging.error(exc)
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()  # pragma: no cover
