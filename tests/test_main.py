"""
Test pakit.main
"""
from __future__ import absolute_import

import mock
import os
import pytest

from pakit.exc import PakitError
from pakit.main import args_parser, main, parse_tasks, write_config
from pakit.recipe import RecipeDB
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask
)
import pakit.task
import tests.common as tc


class TestWriteConfig(object):
    def setup(self):
        self.config = tc.env_setup()
        self.conf_file = os.path.join(tc.STAGING, 'conf.yaml')

    def teardown(self):
        tc.delete_it(self.conf_file)

    @mock.patch('pakit.main.sys')
    def test_write_config(self, mock_sys):
        assert not os.path.exists(self.conf_file)
        main(['pakit', '--conf', self.conf_file, '--create-conf'])
        assert os.path.exists(self.conf_file)
        assert mock_sys.exit.called

    def test_write_config_dir(self):
        os.mkdir(self.conf_file)
        self.config.filename = self.conf_file
        with pytest.raises(PakitError):
            write_config(self.config)

    @mock.patch('pakit.main.sys')
    def test_write_config_perms(self, mock_sys):
        self.conf_file = '/ttt.yaml'
        with pytest.raises(PakitError):
            main(['pakit', '--conf', self.conf_file, '--create-conf'])
        assert mock_sys.exit.called


class TestArgs(object):
    def setup(self):
        self.parser = args_parser()

    def test_no_args(self):
        args = self.parser.parse_args([])
        assert args.install is None
        assert args.remove is None
        assert args.update is False
        assert args.list is False
        assert args.available is False
        assert args.display is None
        assert args.search is None

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
        assert args.update

    def test_args_list(self):
        parser = args_parser()
        args = parser.parse_args('--list'.split())
        assert args.list

    def test_args_list_short(self):
        parser = args_parser()
        args = parser.parse_args('--list-short'.split())
        assert args.list_short

    def test_args_available(self):
        parser = args_parser()
        args = parser.parse_args('--available'.split())
        assert args.available

    def test_args_available_short(self):
        parser = args_parser()
        args = parser.parse_args('--available-short'.split())
        assert args.available_short

    def test_args_display(self):
        parser = args_parser()
        args = parser.parse_args('--display ag vim'.split())
        assert args.display == ['ag', 'vim']

    def test_args_search(self):
        parser = args_parser()
        args = parser.parse_args('--search ag vim'.split())
        assert args.search == ['ag', 'vim']


class TestParseTasks(object):
    def setup_class(self):
        tc.CONF = None
        self.config = tc.env_setup()
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
        recipe = RecipeDB().get('ag')
        pakit.task.IDB.add(recipe)
        args = self.parser.parse_args('--update'.split())
        tasks = parse_tasks(args)
        assert UpdateTask(recipe.name) in tasks
        pakit.task.IDB.remove(recipe.name)

    def test_parse_list(self):
        args = self.parser.parse_args('--list'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListInstalled)
        assert tasks[0].short is False

    def test_parse_list_short(self):
        args = self.parser.parse_args('--list-short'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListInstalled)
        assert tasks[0].short

    def test_parse_available(self):
        args = self.parser.parse_args('--available'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListAvailable)
        assert tasks[0].short is False

    def test_parse_available_short(self):
        args = self.parser.parse_args('--available-short'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], ListAvailable)
        assert tasks[0].short

    def test_parse_display(self):
        args = self.parser.parse_args('--display ag'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], DisplayTask)

    def test_parse_search(self):
        args = self.parser.parse_args('--search ag'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], SearchTask)


class TestMain(object):
    """ Test different argv's passed to main. """
    @classmethod
    def setup_class(cls):
        tc.env_setup()

    @classmethod
    def teardown_class(cls):
        tc.env_teardown()
        tc.CONF = None
        tc.env_setup()

    @mock.patch('pakit.main.PLOG')
    def test_normal_args(self, mock_plog):
        main(['pakit', '--list'])
        assert mock_plog.info.called

    @mock.patch('pakit.main.sys')
    def test_args_none(self, mock_sys):
        main(['pakit'])
        mock_sys.exit.assert_called_with(1)

    @mock.patch('pakit.main.argparse._sys')
    def test_args_bad(self, mock_argsys):
        """ NB: I mock argparse._sys, preventing the short circuit
            sys.exit that would stop code, hence hitting two sys.exits. """
        main(['pakit', 'hello'])
        mock_argsys.exit.assert_called_with(2)

    @mock.patch('pakit.main.PLOG')
    def test_no_update_needed(self, mock_plog):
        main(['pakit', '--update'])
        mock_plog.info.assert_called_with('Nothing to update.')

    @mock.patch('pakit.main.parse_tasks')
    def test_pakit_error(self, mock_parse):
        mock_parse.side_effect = PakitError('Just throw.')
        with pytest.raises(PakitError):
            main(['pakit', '--list'])

    @mock.patch('pakit.main.PLOG')
    def test_recipe_not_found(self, mock_plog):
        expect = 'Missing recipe to build: iiiii'
        main(['pakit', '-i', 'iiiii'])
        mock_plog.info.assert_called_with(expect)
