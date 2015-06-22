""" The obligatory main entry point. """
from __future__ import absolute_import

import argparse
import glob
import logging
import os
import shutil
import sys

from formula import Ag
from wok.conf import Config
from wok import __version__

def select_action(args, config):
    ret = None
    if args.install is not None:
        ret = InstallAction(config=config, progs=args.install)
    elif args.remove is not None:
        ret = RemoveAction(config=config, progs=args.remove)
    elif args.update is True:
        ret = UpdateAction(config=config)
    elif args.list is True:
        ret = ListAction(config=config)

    return ret

class InstallAction(object):
    def __init__(self, **kwargs):
        self.__config = kwargs.get('config')
        self.__progs = kwargs.get('install', [])

    def __call__(self):
        try:
            logging.debug('Install Action')
            task_d = os.path.join(self.__config.install_to, Ag.__name__.lower())
            task = Ag(task_d)
            task.download()
            task.build()
            task.clean()
            self.walk_and_link(task_d, self.__config.link_to)
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
                    logging.error('Could not symlink %s -> %s'.format(sfile, dfile))

class RemoveAction(object):
    def __init__(self, **kwargs):
        self.__config = kwargs.get('config')
        self.__progs = kwargs.get('remove', [])

    def __call__(self):
        try:
            logging.debug('Remove Action')
            task_d = os.path.join(self.__config.install_to, Ag.__name__.lower())
            self.walk_and_remove(task_d, self.__config.link_to)
            shutil.rmtree(task_d)
        except OSError as exc:
            logging.error(exc)

    def walk_and_remove(self, src, dst):
        """ Before removing program, take care of links. """
        for dirpath, _, filenames in os.walk(src, topdown=False, followlinks=True):
            link_dst = os.path.join(dst, dirpath.replace(src + '/', ''))
            for fname in filenames:
                os.remove(os.path.join(link_dst, fname))

            try:
                os.rmdir(link_dst)
            except OSError:
                pass

class UpdateAction(object):
    def __init__(self, **kwargs):
        self.__config = kwargs.get('config')

    def __call__(self):
        try:
            logging.debug('Update Action')
            self.__progs = glob.glob(os.path.join(self.__config.install_d, '*'))
        except OSError as exc:
            logging.error(exc)

class ListAction(object):
    def __init__(self, **kwargs):
        self.__config = kwargs.get('config')

    def __call__(self):
        logging.debug('List Action')

def dir_check(config):
    for dirname in [config.install_to, config.link_to]:
        try:
            os.makedirs(dirname)
        except OSError:
            pass

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
    parser.add_argument('-w', '--wokinit',
                        default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    mut1 = parser.add_mutually_exclusive_group()
    mut1.add_argument('-i', '--install', nargs='+',
                        metavar='PROG', help='install specified program(s)')
    mut1.add_argument('-r', '--remove', nargs='+',
                        metavar='PROG', help='remove specified program(s)')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                        help='update installed program(s)')

    # Require at least one for now.
    if len(sys.argv) == 1:
        parser.print_usage()
        logging.error('No arguments. What should I do?')
        sys.exit(1)

    args = parser.parse_args()
    logging.debug('CLI: %s', args)

    config = Config(args.wokinit)
    logging.debug('Wok Config: %s', config)

    dir_check(config)

    inst = select_action(args, config)
    inst()

if __name__ == '__main__':
    main()
