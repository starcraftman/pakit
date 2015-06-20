#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import

import argparse
import logging
import os
import shutil
import sys

from formula import Ag
from wok.conf import Config

class Installer(object):
    def __init__(self, args, config):
        self.action = None
        self.__progs = []
        self.__choose_action(args)
        self.__link_d = config.link_to
        self.__install_d = config.install_to

    def __str__(self):
        action = None
        if self.action is not None:
            action = self.action.__name__
        return '{0} : {1}'.format(action, self.__progs)

    def __choose_action(self, args):
        """ Primitive strategy selection. """
        if args.install is not None:
            self.action = self.install
            self.__progs = args.install
        elif args.remove is not None:
            self.action = self.remove
            self.__progs = args.remove
        elif args.update is True:
            self.action = self.update

    def install(self):
        task_d = os.path.join(self.__install_d, Ag.__name__.lower())
        task = Ag(task_d)
        task.download()
        task.build()
        task.clean()
        self.walk_and_link(task_d, self.__link_d)
        return task.verify()

    def remove(self):
        try:
            task_d = os.path.join(self.__install_d, Ag.__name__.lower())
            self.walk_and_remove(task_d, self.__link_d)
            shutil.rmtree(task_d)
        except OSError:
            pass

    def update(self):
        return 'update'
        #progs = glob.glob(os.path.join(self.__install_d, '*'))

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
                    pass

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

def dir_check(config):
    for dirname in [config.install_to, config.link_to]:
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
        os.makedirs(dirname)

# TODO: Path modification during operation by os.environ
def main():
    # TODO: Add choices kwarg for install/remove based on avail formula
    mesg = """wok is a homebrew like installer.

    Available Programs:
    """
    parser = argparse.ArgumentParser(description=mesg,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)
    parser.add_argument('-w', '--wokinit',
                        default=os.path.expanduser('~/.wok.yaml'),
                        help='yaml config file')
    mut1 = parser.add_mutually_exclusive_group()
    mut1.add_argument('-i', '--install', nargs='+',
                        metavar='PROG', help='install specified programs')
    mut1.add_argument('-r', '--remove', nargs='+',
                        metavar='PROG', help='remove specified programs')
    mut1.add_argument('-u', '--update', default=False, action='store_true',
                        help='update installed programs')

    # Require at least one for now.
    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()
    logging.debug('CLI: %s', args)

    config = Config(args.wokinit)
    logging.debug('Wok Config: %s', config)

    dir_check(config)

    inst = Installer(args, config)
    print(inst)
    inst.action()

if __name__ == '__main__':
    main()
