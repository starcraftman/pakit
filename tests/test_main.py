""" To be used at some point. Maybe?"""
from __future__ import absolute_import, print_function

import os
# import pytest

from wok.main import *
from wok.shell import Command
from wok.task import *
import wok.task

class TestArgs(object):
    def setup(self):
        self.parser = args_parser()

    def test_no_args(self):
        args = self.parser.parse_args([])
        assert args.install is None
        assert args.remove is None
        assert args.update is False
        assert args.list is False

    def test_args_install(self):
        args = self.parser.parse_args('--install ag tmux'.split())
        assert args.install == ['ag', 'tmux']

    def test_args_remove(self):
        parser = args_parser()
        args = parser.parse_args('--remove ag'.split())
        assert args.remove == ['ag']

    def test_args_update(self):
        parser = args_parser()
        args = parser.parse_args('--update'.split())
        assert args.update is True

    def test_args_list(self):
        parser = args_parser()
        args = parser.parse_args('--list'.split())
        assert args.list is True


class TestParseTasks(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'wok.yaml')
        self.config = global_init(config_file)
        self.parser = args_parser()

    def test_parse_install(self):
        args = self.parser.parse_args('--install ag'.split())
        tasks = parse_tasks(args)
        assert tasks[0] == InstallTask('ag')
        assert isinstance(tasks[0], InstallTask)

    def test_parse_remove(self):
        args = self.parser.parse_args('--remove ag'.split())
        tasks = parse_tasks(args)
        assert tasks[0] == RemoveTask('ag')
        assert isinstance(tasks[0], RemoveTask)

    def test_parse_update(self):
        # Need yaml file to trick into thinking installed
        recipe = RecipeDB().get('ag')
        wok.task.IDB.add(recipe)
        args = self.parser.parse_args('--update'.split())
        tasks = parse_tasks(args)
        assert tasks[0] == UpdateTask('ag')
        assert isinstance(tasks[0], UpdateTask)
        Command('rm -rf ' + self.config.get('paths.prefix')).wait()

    def test_parse_list(self):
        args = self.parser.parse_args('--list'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListInstalled)

class TestArgv(object):
    """ Do end to end testing on main(). """
    pass
