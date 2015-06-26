""" The obligatory main entry point. """
from __future__ import absolute_import, print_function

import argparse
import logging
import os
import shutil
import sys

from formula import *
from wok.conf import Config
from wok import __version__

def select_action(args, paths):
    if args.install is not None:
        ret = InstallAction(paths=paths, progs=args.install)
    elif args.remove is not None:
        ret = RemoveAction(paths=paths, progs=args.remove)
    elif args.update is True:
        ret = UpdateAction(paths=paths)
    elif args.list is True:
        ret = ListAction(paths=paths)
    else:
        ret = None

    return ret

class InstallAction(object):
    def __init__(self, **kwargs):
        self.__paths = kwargs.get('paths')
        self.__progs = kwargs.get('progs', [])
        logging.debug(str(kwargs))
        logging.debug(self.__paths)

    def __call__(self):
        for name in self.__progs:
            self.install(name)

    def install(self, name):
        try:
            logging.debug('Install Action {0}'.format(name))
            cls = import_recipe(name)
            task_d = os.path.join(self.__paths.get('prefix'),
                    cls.__name__.lower())
            task = cls(task_d)
            task.download()
            task.build()
            task.clean()
            self.walk_and_link(task_d, self.__paths.get('link'))
            return task.verify()
        except OSError as exc:
            logging.error(exc)

    def walk_and_link(self, src, dst):
        """ Link a program to dst. """
        for dirpath, _, filenames in os.walk(src, followlinks=True):
            link_dst = os.path.join(dst, dirpath.replace(src + '/', ''))
            try:
                os.makedirs(link_dst)
            except OSError:
                pass

            for fname in filenames:
                try:
                    sfile = os.path.join(dirpath, fname)
                    dfile = os.path.join(link_dst, fname)
                    os.symlink(sfile, dfile)
                except OSError:
                    logging.error('Could not symlink {0} -> {1}'.format(sfile,
                            dfile))

class RemoveAction(object):
    def __init__(self, **kwargs):
        self.__paths = kwargs.get('paths')
        self.__progs = kwargs.get('progs', [])

    def __call__(self):
        for name in self.__progs:
            self.remove(name)

    def remove(self, name):
        try:
            cls = import_recipe(name)
            task_d = os.path.join(self.__paths.get('prefix'),
                    cls.__name__.lower())
            self.walk_and_unlink(task_d, self.__paths.get('link'))
            shutil.rmtree(task_d)
        except OSError as exc:
            logging.error(exc)

    def walk_and_unlink(self, src, dst):
        """ Before removing program, take care of links. """
        for dirpath, _, filenames in os.walk(src,
                topdown=False, followlinks=True):
            link_dst = os.path.join(dst, dirpath.replace(src + '/', ''))
            for fname in filenames:
                os.remove(os.path.join(link_dst, fname))

            try:
                os.rmdir(link_dst)
            except OSError:
                pass

class UpdateAction(object):
    def __init__(self, **kwargs):
        self.__paths = kwargs.get('paths')

    def __call__(self):
        try:
            logging.debug('Update Action')
            progs = os.listdir(self.__paths.get('prefix'))
        except OSError as exc:
            logging.error(exc)

class ListAction(object):
    def __init__(self, **kwargs):
        self.__paths = kwargs.get('paths')

    def __call__(self):
        logging.debug('List Action')
        try:
            installed = os.listdir(self.__paths.get('prefix'))
            print("The following programs are installed:")
            for prog in installed:
                print('*', prog)
            return installed
        except OSError as exc:
            logging.error(exc)

def dir_check(paths):
    for dirname in [paths.get('prefix'), paths.get('link'), paths.get('source')]:
        try:
            os.makedirs(dirname)
        except OSError:
            pass

def import_recipe(name):
    """ Return a reference to the class. """
    mod = __import__('formula.' + name)
    mod = getattr(mod, name)
    return getattr(mod, name.capitalize())

# TODO: Path modification during operation by os.environ
def main():
    # TODO: Add choices kwarg for install/remove based on avail formula
    mesg = """wok is a homebrew like installer.

    Available Programs:
    """
    parser = argparse.ArgumentParser(description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--version', action='version',
                        version='wok {0}\nALPHA SOFTWARE!'.format(__version__))
    parser.add_argument('-c', '--conf', default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
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
    logging.debug('Wok Config: %s', config)

    dir_check(config.paths)

    try:
        action = select_action(args, config.paths)
        action()
    except TypeError:
        parser.print_usage()
        logging.error('Insufficient arguments. What should I do?')
        sys.exit(1)

if __name__ == '__main__':
    main()
