""" To be used at some point. Maybe?"""
from __future__ import absolute_import

import mock
import os
import pytest

from pakit.main import args_parser, global_init, main, parse_tasks
from pakit.recipe import RecipeDB, RecipeNotFound
from pakit.shell import Command
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable
)
import pakit.task

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

    def test_args_available(self):
        parser = args_parser()
        args = parser.parse_args('--available'.split())
        assert args.available is True

    def test_args_display(self):
        parser = args_parser()
        args = parser.parse_args('--display ag vim'.split())
        assert args.display == ['ag', 'vim']

class TestParseTasks(object):
    def setup(self):
        config_file = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
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
        pakit.task.IDB.add(recipe)
        args = self.parser.parse_args('--update'.split())
        tasks = parse_tasks(args)
        assert tasks[0] == UpdateTask('ag')
        assert isinstance(tasks[0], UpdateTask)
        Command('rm -rf ' + self.config.get('paths.prefix')).wait()

    def test_parse_list(self):
        args = self.parser.parse_args('--list'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListInstalled)

    def test_parse_available(self):
        args = self.parser.parse_args('--available'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListAvailable)

    def test_parse_display(self):
        args = self.parser.parse_args('--display ag'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], DisplayTask)


class TestMain(object):
    """ Test different argv's passed to main. """
    @mock.patch('pakit.main.sys')
    def test_args_none(self, mock_sys):
        main(['pakit'])
        mock_sys.exit.assert_called_with(1)

    @mock.patch('pakit.main.argparse._sys')
    @mock.patch('pakit.main.sys')
    def test_args_bad(self, mock_sys, mock_argsys):
        """ NB: I mock argparse._sys, preventing the short circuit
            sys.exit that would stop code, hence hitting two sys.exits. """
        main(['pakit', 'hello'])
        mock_argsys.exit.assert_called_with(2)
        mock_sys.exit.assert_called_with(1)

    def test_recipe_not_found(self):
        with pytest.raises(RecipeNotFound):
            main(['pakit', '-i', 'iiiii'])

    @mock.patch('pakit.main.sys')
    def test_write_config(self, mock_sys):
        conf_file = './conf.yaml'
        assert not os.path.exists(conf_file)
        main(['pakit', '--conf', conf_file, '--create-conf'])
        assert os.path.exists(conf_file)
        os.remove(conf_file)
