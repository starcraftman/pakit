"""
Test pakit.main
"""
from __future__ import absolute_import

import mock
import os
import pytest
import shutil

import pakit.conf
from pakit.exc import PakitError
from pakit.main import (
    args_parser, main, link_man_page, parse_tasks, search_for_config,
    write_config,
)
from pakit.recipe import RecipeDB
from pakit.task import (
    InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask
)
import tests.common as tc


def test_link_man_page():
    l_dir = os.path.join(tc.STAGING, 'links')
    expected_link = os.path.join(tc.STAGING, 'links', 'share', 'man', 'man1',
                                 'pakit.1')
    link_man_page(l_dir)
    assert os.path.islink(expected_link)
    tc.delete_it(l_dir)


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

        # Preserve these if they exist
        self.home_conf_existed = False
        if os.path.exists(self.home_conf):
            self.home_conf_existed = True
            shutil.move(self.home_conf, self.home_conf + '_bak')
        self.home_pakit_conf_existed = False
        if os.path.exists(self.home_pakit_conf):
            self.home_pakit_conf_existed = True
            shutil.move(self.home_pakit_conf, self.home_pakit_conf + '_bak')

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
        if self.home_conf_existed:
            shutil.move(self.home_conf + '_bak', self.home_conf)
        if self.home_pakit_conf_existed:
            shutil.move(self.home_pakit_conf + '_bak', self.home_pakit_conf)

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
            write_config(self.conf_file)

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
        pakit.conf.IDB.add(recipe)
        args = self.parser.parse_args('--update'.split())
        tasks = parse_tasks(args)
        assert UpdateTask(recipe.name) in tasks
        pakit.conf.IDB.remove(recipe.name)

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
            main(['pakit', '--conf', tc.TEST_CONFIG, '--list'])

    @mock.patch('pakit.main.PLOG')
    def test_recipe_not_found(self, mock_plog):
        expect = 'Missing recipe to build: iiiii'
        main(['pakit', '-i', 'iiiii'])
        mock_plog.info.assert_called_with(expect)
