"""
Test pakit.main
"""
from __future__ import absolute_import

import copy
import mock
import os
import pytest
import shutil

import pakit.conf
import pakit.recipe
from pakit.exc import PakitError
from pakit.main import (
    create_args_parser, environment_check, main, link_man_pages, parse_tasks,
    search_for_config, order_tasks, write_config
)
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask, RelinkRecipes
)
import tests.common as tc


def test_link_man_pages():
    try:
        link_dir = os.path.join(tc.STAGING, 'links')
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'pakit', 'extra')
        fake_man = os.path.join(src, 'test_man.1')

        try:
            os.makedirs(os.path.dirname(fake_man))
        except OSError:
            pass
        with open(fake_man, 'w') as fout:
            fout.write('hello')

        link_man_pages(link_dir)
        expected_man = os.path.join(link_dir, 'share', 'man', 'man1',
                                    os.path.basename(fake_man))
        assert os.path.islink(expected_man)
    finally:
        tc.delete_it(fake_man)
        tc.delete_it(link_dir)


@mock.patch('pakit.main.PLOG')
def test_environment_check(mock_log):
    bin_dir = os.path.join(tc.CONF.path_to('link'), 'bin')
    old_path = os.environ['PATH']
    os.environ['PATH'] = os.environ['PATH'].replace(bin_dir, '')

    environment_check(tc.CONF)
    mock_log.assert_called_with('  For Most Shells: export PATH=%s:$PATH',
                                bin_dir)

    os.environ['PATH'] = old_path


class TestSearchConfig(object):
    def setup(self):
        self.orig_dir = os.getcwd()
        self.test_dir = os.path.join(tc.STAGING, 'first')
        self.first_conf = os.path.join(self.test_dir, '.pakit.yml')
        self.second_conf = os.path.join(self.test_dir, 'second', 'pakit.yaml')
        self.third_conf = os.path.join(self.test_dir, 'second', 'third',
                                       'pakit.yml')
        self.home_conf = os.path.join(os.path.expanduser('~'), '.pakit.yml')
        self.home_pakit_conf = os.path.join(os.path.expanduser('~'), '.pakit',
                                            '.pakit.yaml')

        os.makedirs(os.path.dirname(self.third_conf))
        try:
            os.makedirs(os.path.dirname(self.home_pakit_conf))
        except OSError:
            pass
        for path in [self.first_conf, self.second_conf, self.third_conf,
                     self.home_conf, self.home_pakit_conf]:
            shutil.copy(tc.TEST_CONFIG, path)
        os.chdir(os.path.dirname(self.third_conf))

    def teardown(self):
        os.chdir(self.orig_dir)
        tc.delete_it(self.test_dir)
        tc.delete_it(self.home_conf)
        tc.delete_it(self.home_pakit_conf)

    def test_search_config_cur_dir(self):
        assert search_for_config() == self.third_conf

    def test_search_config_one_up(self):
        tc.delete_it(self.third_conf)
        assert search_for_config() == self.second_conf

    def test_search_config_two_up(self):
        tc.delete_it(self.third_conf)
        tc.delete_it(self.second_conf)
        assert search_for_config() == self.first_conf

    def test_search_config_home(self):
        tc.delete_it(self.third_conf)
        tc.delete_it(self.second_conf)
        tc.delete_it(self.first_conf)
        assert search_for_config() == self.home_conf

    def test_search_config_home_pakit(self):
        tc.delete_it(self.third_conf)
        tc.delete_it(self.second_conf)
        tc.delete_it(self.first_conf)
        tc.delete_it(self.home_conf)
        assert search_for_config() == self.home_pakit_conf

    def test_search_config_default(self):
        tc.delete_it(self.third_conf)
        tc.delete_it(self.second_conf)
        tc.delete_it(self.first_conf)
        tc.delete_it(self.home_conf)
        tc.delete_it(self.home_pakit_conf)
        assert search_for_config(1) == 1


class TestWriteConfig(object):
    def setup(self):
        self.old_rdb = pakit.recipe.RDB
        self.old_conf = pakit.conf.CONFIG
        self.conf_file = os.path.join(tc.STAGING, 'conf.yaml')

    def teardown(self):
        tc.delete_it(self.conf_file)
        pakit.conf.CONFIG = self.old_conf
        pakit.recipe.RDB = self.old_rdb

    @mock.patch('pakit.main.sys')
    def test_write_config(self, mock_sys):
        assert not os.path.exists(self.conf_file)
        main(['pakit', '--conf', self.conf_file, '--create-conf'])
        assert os.path.exists(self.conf_file)
        assert mock_sys.exit.called

    def test_write_config_dir(self):
        os.mkdir(self.conf_file)
        config = copy.deepcopy(tc.CONF)
        config.filename = self.conf_file
        with pytest.raises(PakitError):
            write_config(self.conf_file)

    @mock.patch('pakit.main.sys')
    def test_write_config_perms(self, mock_sys):
        self.conf_file = '/ttt.yaml'
        with pytest.raises(PakitError):
            main(['pakit', '--conf', self.conf_file, '--create-conf'])
        assert mock_sys.exit.called


class TestArgs(object):
    def setup(self):
        self.parser = create_args_parser()

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
        args = self.parser.parse_args('--remove ag'.split())
        assert args.remove == ['ag']

    def test_args_update(self):
        args = self.parser.parse_args('--update'.split())
        assert args.update

    def test_args_list(self):
        args = self.parser.parse_args('--list'.split())
        assert args.list

    def test_args_list_short(self):
        args = self.parser.parse_args('--list-short'.split())
        assert args.list_short

    def test_args_available(self):
        args = self.parser.parse_args('--available'.split())
        assert args.available

    def test_args_available_short(self):
        args = self.parser.parse_args('--available-short'.split())
        assert args.available_short

    def test_args_display(self):
        args = self.parser.parse_args('--display ag vim'.split())
        assert args.display == ['ag', 'vim']

    def test_args_relink(self):
        args = self.parser.parse_args('--relink'.split())
        assert args.relink

    def test_args_search(self):
        args = self.parser.parse_args('--search ag vim'.split())
        assert args.search == ['ag', 'vim']


class TestOrderTasks(object):
    def test_no_requires(self):
        tasks = order_tasks(['providesb'], InstallTask)
        assert len(tasks) == 1
        assert tasks[0] == InstallTask('providesb')

    def test_requirements_possible(self):
        tasks = order_tasks(['dependsonb'], InstallTask)
        assert len(tasks) == 2
        assert tasks[0] == InstallTask('providesb')
        assert tasks[1] == InstallTask('dependsonb')

    def test_requirements_impossible(self):
        with pytest.raises(PakitError):
            order_tasks(['cyclea'], InstallTask)


class TestParseTasks(object):
    def setup(self):
        self.parser = create_args_parser()

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
        """
        Not ideal, but mucking around internally saves hassle.
        """
        recipe_name = 'ag'
        pakit.conf.IDB.conf = {recipe_name: None}

        args = self.parser.parse_args('--update'.split())
        tasks = parse_tasks(args)
        assert UpdateTask(recipe_name) in tasks

        pakit.conf.IDB._conf = {}

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

    def test_parse_relink(self):
        args = self.parser.parse_args('--relink'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], RelinkRecipes)

    def test_parse_search(self):
        args = self.parser.parse_args('--search ag'.split())
        tasks = parse_tasks(args)
        assert isinstance(tasks[0], SearchTask)


class TestMain(object):
    """ Test different argv's passed to main. """
    @mock.patch('pakit.main.PLOG')
    def test_normal_args(self, mock_plog):
        main(['pakit', '--conf', tc.TEST_CONFIG, '--list'])
        assert mock_plog.called

    @mock.patch('pakit.main.sys')
    def test_args_none(self, mock_sys):
        main(['pakit'])
        mock_sys.exit.assert_called_with(1)

    @mock.patch('pakit.main.argparse._sys')
    def test_args_bad(self, mock_argsys):
        """ NB: I mock argparse._sys, preventing the short circuit
            sys.exit that would stop code, hence hitting two sys.exits. """
        main(['pakit', '--conf', tc.TEST_CONFIG, 'hello'])
        mock_argsys.exit.assert_called_with(2)

    @mock.patch('pakit.main.PLOG')
    def test_no_update_needed(self, mock_plog):
        main(['pakit', '--conf', tc.TEST_CONFIG, '--update'])
        mock_plog.assert_called_with('Nothing to update.')

    @mock.patch('pakit.main.parse_tasks')
    def test_pakit_error(self, mock_parse):
        mock_parse.side_effect = PakitError('Just throw.')
        with pytest.raises(PakitError):
            main(['pakit', '--conf', tc.TEST_CONFIG, '--list'])

    @mock.patch('pakit.main.PLOG')
    def test_recipe_not_found(self, mock_plog):
        expect = 'Missing recipe to build: iiiii'
        main(['pakit', '--conf', tc.TEST_CONFIG, '-i', 'iiiii'])
        mock_plog.assert_called_with(expect)
