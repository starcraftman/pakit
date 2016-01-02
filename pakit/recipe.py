"""
The Recipe class and RecipeDB are found here.

DecChangeDir: Deocrate a method, it executes in a different CWD.
DecPrePost: Execute optional pre/post methods.
Recipe: The base class for all recipes.
RecipeDB: The database that indexes all recipes.
RecipeManager: Retrieves and manages remote recipe sources.
"""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import copy
import functools
import glob
import inspect
import logging
import os
import shutil
import sys
import tempfile

try:
    from importlib import reload as ireload
except ImportError:
    from imp import reload as ireload

from pakit.conf import RecipeURIDB
from pakit.exc import PakitDBError, PakitError
from pakit.shell import Command, vcs_factory


PLOG = logging.getLogger('pakit').info
RDB = None


def check_package(path):
    """
    Ensure the path is a valid python module to import from.

    Args:
        path: The path of a python module to check.

    Raises:
        PakitDBError: When the package name is invalid, user must correct.
    """
    if not os.path.isdir(path):
        return

    if os.path.basename(path)[0] == '.':
        raise PakitDBError('Cannot index invalid recipe location. '
                           'Remove the leading period(s) from ' + path)

    init = os.path.join(path, '__init__.py')
    if not os.path.exists(init):
        with open(init, 'w') as fout:
            fout.write('# Written by pakit to mark this folder'
                       'as a python module')


class DecChangeDir(object):  # pylint: disable=too-few-public-methods
    """
    Change the directory to a new one before executing the decorated
    method. Regardless of function outcome, return to old CWD.

    Before calling the wrapped function guarantee...
        1) tempdir created if requested.
        2) working directory is changed to new_cwd.

    After calling the wrapped function guarantee...
        1) working directory is restored to old_cwd.
        2) If tempdir created, remove everything under it.
    """
    def __init__(self, new_cwd=None, use_tempd=False, attr=None):
        """
        Args:
            attr: Read the value of this attribute to get new_cwd.
            new_cwd: Change directory to this path.
            use_tempd: Create a temporary directory and cd into it.
        """
        self.attr = attr
        self.new_cwd = new_cwd
        self.old_cwd = None
        self.use_tempd = use_tempd

    def __call__(self, func):
        """
        The decorator itself.

        Args:
            func: The target to wrap.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            The inner part of the decorator.
            """
            if self.attr:
                self.new_cwd = getattr(args[0], self.attr, self.new_cwd)

            with self:
                func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        """
        Modify the CWD as requested.
        """
        self.old_cwd = os.getcwd()
        if self.use_tempd:
            self.new_cwd = tempfile.mkdtemp(prefix='pakit_tmp_')
        os.chdir(self.new_cwd)

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Undo the change to CWD.
        """
        os.chdir(self.old_cwd)
        if self.use_tempd:
            shutil.rmtree(self.new_cwd)


class DecPrePost(object):  # pylint: disable=too-few-public-methods
    """
    Decorate a method and allow optional pre and post functions to
    execute.

    To be clear, if this decorator is applied to Worker.run,
    the 'pre_func' would be 'Worker.pre_run' and the 'post_func'
    would be 'Worker.post_run'..

    The post_func called only if no exception raised in func.
    """
    def __call__(self, func):
        """
        The decorator itself.

        Args:
            func: The target to wrap.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            The inner part of the decorator.
            """
            pre_func = getattr(args[0], 'pre_' + func.__name__, None)
            post_func = getattr(args[0], 'post_' + func.__name__, None)

            if pre_func:
                PLOG("Executing '%s()' before '%s()'", pre_func.__name__,
                     func.__name__)
                pre_func()

            PLOG("Executing '%s()'", func.__name__)
            func(*args, **kwargs)

            if post_func:
                PLOG("Executing '%s()' after '%s()'", post_func.__name__,
                     func.__name__)
                post_func()

        return wrapper


class Recipe(object):
    """
    A recipe to build some binary through a series of commands.

    *description* and *more_info* are based on the class's __doc__ string.
        description: The first non blank line in __doc__
        more_info: The second non blank line to end of __doc__

    Attributes:
        description: A short description that summarizes the recipe.
            Keep it short, less than 50 chars suggested.
        more_info: A longer description, may take several lines.
        homepage: The website that hosts the project.
        repos: A dictionary that stores all possible methods to retrieve
            source code. By convention, should contain a *stable* and
            *unstable* entry.
        opts: A dictionary storing options for the recipe, to be
            used primarily in the build() commands. See 'cmd' method.
        repo: The active source repository.
        repo_name: The name of the current repository in *repos*.
        name: The name of the recipe.
        install_dir: Where the program will be installed to.
        link_dir: Where the installation will be linked to.
        source_dir: Where the source code will be downloaded to and built.
    """
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Recipe, self).__init__()
        self.homepage = None
        self.opts = {}
        self.repos = None

    def __str__(self):
        """
        A one line summary of the recipe.
        """
        return '{0:10}   {1}'.format(self.name[0:10], self.description)

    def info(self):
        """
        A detailed description of the recipe.
        """
        tab = '  '
        fmt = [
            '{name}',
            'Description: {desc}',
            'Homepage: {home}',
            'Requires: {reqs}',
            'Current Repo: "{cur_repo}"',
        ]
        for name, repo in sorted(self.repos.items()):
            fmt += ['Repo "' + name + '":', '{tab}' + str(repo)]
        if self.more_info:
            fmt += ['More Information:']
            fmt += [tab + line for line in self.more_info]
        str_fmt = '\n  '.join(fmt)
        info = str_fmt.format(name=self.name,
                              desc=self.description,
                              home=self.homepage,
                              reqs=','.join(getattr(self, 'requires', [''])),
                              cur_repo=self.repo_name,
                              tab=tab)
        return info.rstrip('\n')

    def set_config(self, config):
        """
        Query the config for the required opts.

        Users should not be using this directly.
        """
        self.opts.update(config.opts_for(self.name))
        self.opts.update({
            'prefix': os.path.join(self.opts.get('prefix'), self.name),
            'source': os.path.join(self.opts.get('source'), self.name)
        })
        for repo in self.repos.values():
            repo.target = self.source_dir

    @property
    def description(self):
        """
        Return a one line description of the program.
        """
        lines = [line for line in self.__doc__.split('\n') if line != '']

        return lines[0].strip()

    @property
    def more_info(self):
        """
        Return a longer description of the program.
        """
        first_non_blank = True
        rest = None
        lines = self.__doc__.split('\n')

        # Start at second non blank line
        for num, line in enumerate(lines):
            line = line.strip()
            if line and first_non_blank:
                first_non_blank = False
                continue
            if line:
                rest = [sline.strip() for sline in lines[num:]]
                break

        # Remove trailing blank lines
        if rest:
            index = len(rest)
            reversed_rest = list(reversed(rest))
            for num, line in enumerate(reversed_rest):
                if line:
                    index = num
                    break
            rest = list(reversed(reversed_rest[index:]))

        return rest

    @property
    def install_dir(self):
        """
        The folder the program will install to.
        """
        return self.opts.get('prefix')

    @property
    def link_dir(self):
        """
        The folder the program will be linked to.
        """
        return self.opts.get('link')

    @property
    def source_dir(self):
        """
        The folder where the source will download & build.
        """
        return self.opts.get('source')

    @property
    def name(self):
        """
        The name of the recipe.
        """
        return self.__class__.__name__.lower()

    @property
    def repo(self):
        """
        The *Fetchable* class providing the source code.
        """
        return self.repos.get(self.repo_name)

    @repo.setter
    def repo(self, new_repo):
        """
        Set the repository for the source code.

        Args:
            new_repo: A key in *repos*.
        """
        if new_repo not in self.repos:
            raise KeyError('Build repository not available.')
        self.opts['repo'] = new_repo
        if os.path.exists(self.source_dir):
            self.repo.clean()

    @property
    def repo_name(self):
        """
        The name of the repository in *repos*.
        """
        return self.opts.get('repo')

    def cmd(self, cmd, **kwargs):
        """
        Wrapper around pakit.shell.Command. Behaves the same except:

        - Expand all dictionary markers in *cmd* against *self.opts*.
            Arg *cmd* may be a string or a list of strings.
        - If no *cmd_dir* in kwargs, then execute in current directory.
        - If no *timeout* in kwargs, use default pakit Command timeout.
        - Command will block until completed or Exception raised.

        Args:
            cmd: A string or list of strings that forms the command.
                 Dictionary markers like '{prefix}' will be expanded
                 against self.opts.

        Kwargs:
            cmd_dir: The directory to execute command in.
            prev_cmd: The previous Command, use it for stdin.
            timeout: When no stdout/stderr recieved for timeout
                     kill command and raise exception.

        Returns:
            Command object that was running as a subprocess.

        Raises:
            PakitCmdError: The return code indicated failure.
            PakitCmdTimeout: The timeout interval was reached.
        """
        if isinstance(cmd, type('')):
            cmd = cmd.format(**self.opts)
        else:
            cmd = [word.format(**self.opts) for word in cmd]

        timeout = kwargs.pop('timeout', None)

        cmd_dir = kwargs.get('cmd_dir', os.getcwd())
        PLOG('Executing in %s: %s', cmd_dir, cmd)
        cmd = Command(cmd, **kwargs)

        if timeout:
            cmd.wait(timeout)
        else:
            cmd.wait()

        return cmd

    @abstractmethod
    def build(self):
        """
        Build the program from the source directory.

        Should make use of the 'cmd' method to execute system commands.

        Can put build specific commands based on repo_name.

        Raises:
            PakitCmdError: A Command returned an error.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self):
        """
        Use `assert` statements to verify the built program works.

        Raises:
            AssertionError: When an assertion fails.
        """
        raise NotImplementedError


class RecipeDB(object):
    """
    An object database that can import recipes dynamically.
    """
    def __init__(self, config):
        self.config = config
        self.rdb = {}

    def __contains__(self, name):
        return name in self.rdb

    def __iter__(self):
        for key in sorted(self.rdb):
            yield (key, self.rdb[key])

    def get(self, name):
        """
        Get the recipe from the database.

        Raises:
            PakitDBError: Could not resolve the name to a recipe.
        """
        obj = self.rdb.get(name)
        if obj is None:
            raise PakitDBError('Missing recipe to build: ' + name)
        return obj

    def index(self, path):
        """
        Index all *Recipes* in the path.

        For each file, the Recipe subclass should be named after the file.
        So for path/ag.py should have a class called Ag.

        Args:
            path: The folder containing recipes to index.
        """
        try:
            check_package(path)
            sys.path.insert(0, os.path.dirname(path))

            new_recs = [inspect.getmodulename(fname) for fname
                        in glob.glob(os.path.join(path, '*.py'))]
            if '__init__' in new_recs:
                new_recs.remove('__init__')
            if 'setup' in new_recs:
                new_recs.remove('setup')

            mod = os.path.basename(path)
            for cls in new_recs:
                obj = self.recipe_obj(mod, cls)
                self.rdb.update({cls: obj})
        finally:
            if os.path.dirname(path) in sys.path:
                sys.path.remove(os.path.dirname(path))

    def names(self, desc=False):
        """
        Names of recipes available, optionally with descriptions.

        Args:
            desc:
                When True, return a list of recipe names and descriptions.
                When False, return a list of recipe names and descriptions.

        Returns:
            A list of strings. By default the names of all recipes.
            Otherwise, it is a list of recipes and their description.
        """
        if desc:
            return sorted([str(recipe) for recipe in self.rdb.values()])
        else:
            return sorted(self.rdb.keys())

    def recipe_obj(self, mod_name, cls_name):
        """
        Import and instantiate the recipe class. Then configure it.

        Args:
            mod_name: The module name, should be importable via PYTHONPATH.
            cls_name: The name of the submodule.
                    Submodule should contain subclass of pakit.recipe.Recipe.

        Returns:
            The instantiated recipe.

        Raises:
            AttributeError: The module did not have the required class.
            ImportError: If the module could not be imported.
        """
        # FIXME: Work around to prevent multiple decorations.
        #        Recipes should be reloadable given current format.
        mod = ireload(getattr(__import__(mod_name + '.' + cls_name), cls_name))
        for member in inspect.getmembers(mod, inspect.isclass):
            if member[0] != 'Recipe' and issubclass(member[1], Recipe):
                cls = member[1]
                break

        cls.build = DecChangeDir(attr='source_dir')(DecPrePost()(cls.build))
        cls.verify = DecChangeDir(use_tempd=True)(DecPrePost()(cls.verify))
        obj = cls()
        obj.set_config(self.config)
        return obj


class RecipeManager(object):
    """
    Manage the retrieval and updating of recipe sources remote and local.
    This class works in conjunction with RecipeDB to provide recipes to pakit.

    Attributes:
        active_kwargs: Indexed on uri, value is kwargs for the factory.
        active_uris: Actively configured sources.
        root: Where all recipes will be downloaded and stored.
        uri_db: A database to help keep track of recipe sources.
            Indexed based on uri.
    """
    def __init__(self, config):
        """
        Initialize the state of the Recipe manager based on configuration.

        Args:
            config: The pakit configuration.
        """
        self.interval = config.get('pakit.recipe.update_interval')
        self.root = config.path_to('recipes')
        self.uri_db = RecipeURIDB(os.path.join(self.root, 'uris.yml'))
        self.active_kwargs = {}
        self.active_uris = []
        for kwargs in copy.deepcopy(config.get('pakit.recipe.uris')):
            uri = kwargs.pop('uri')
            self.active_uris.append(uri)
            if len(kwargs):
                self.active_kwargs[uri] = kwargs

    @property
    def paths(self):
        """
        Returns the paths to all active recipe locations on the system.
        """
        return [self.uri_db[uri]['path'] for uri in self.active_uris]

    def check_for_deletions(self):
        """
        Check if any entries in the uri_db are stale.

        Purge any uri_db entries that have been deleted from their path.
        """
        to_remove = []
        for uri, remote in self.uri_db:
            if not os.path.exists(remote['path']):
                to_remove.append(uri)

        for uri in to_remove:
            self.uri_db.remove(uri)
        self.uri_db.write()

    def check_for_updates(self):
        """
        Check if any of the active URIs needs updating.

        A recipe remote will be update if it is version controlled and ...
            - it has not been updated since interval
            - the kwargs between uri_db and active_kwargs differ
        """
        need_updates = self.uri_db.need_updates(self.interval)
        vcs_uris = [uri for uri, entry in self.uri_db if entry['is_vcs']]
        for uri in set(self.active_uris).intersection(vcs_uris):
            db_kwargs = self.uri_db[uri].get('kwargs', {})
            kwargs = self.active_kwargs.get(uri, {})
            repo = vcs_factory(uri, **kwargs)
            repo.target = self.uri_db[uri]['path']

            if uri in need_updates or db_kwargs != kwargs:
                PLOG('Updating recipes from: %s.', uri)
                with repo:
                    self.uri_db.update_time(uri)
                    self.uri_db[uri]['kwargs'] = kwargs

        self.uri_db.write()

    def init_new_uris(self):
        """
        For new uris not present in the uri_db:
            - Select a unique name inside recipes folder
            - Add an entry to the uri_db
            - If the uri is local, create the folder at the path.
            - If the uri is remote, clone the version repository
              with optional kwargs.

        Raises:
            PakitError: User attempted to use an unsupported URI.
        """
        for uri in set(self.active_uris).difference(self.uri_db.conf.keys()):
            repo = None
            kwargs = self.active_kwargs.get(uri, {})

            try:
                repo = vcs_factory(uri, **kwargs)
            except PakitError:
                if uri.find('/') != -1 or uri.find('.') != -1:
                    raise

            preferred = os.path.join(self.root, os.path.basename(uri))
            path = self.uri_db.select_path(preferred)
            self.uri_db.add(uri, path, repo is not None, kwargs)

            if repo:
                repo.target = path
                PLOG('Downloading new recipes: %s', uri)
                with repo:
                    pass
            else:
                PLOG('Indexing local recipes from: %s', path)
                try:
                    os.makedirs(path)
                except OSError:
                    pass

        self.uri_db.write()
