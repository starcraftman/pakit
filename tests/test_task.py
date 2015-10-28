"""
Test pakit.task
"""
from __future__ import absolute_import, print_function

import logging
import mock
import os
import pytest
import shutil

import pakit.conf
import pakit.recipe
from pakit.exc import PakitCmdError, PakitLinkError
from pakit.task import (
    subseq_match, substring_match, Task, RecipeTask,
    InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask, RelinkRecipes
)
import tests.common as tc


def test_subseq_match():
    haystack = 'Hello World!'
    assert subseq_match(haystack, 'hwor')
    assert subseq_match(haystack, 'HeWd')
    assert not subseq_match(haystack, 'Good')


def test_substring_match():
    haystack = 'Hello World!'
    assert substring_match(haystack, 'hello')
    assert substring_match(haystack, 'Hello')
    assert not substring_match(haystack, 'HelloW')


class TestTaskBase(object):
    """ Shared setup, most task tests will want this. """
    def setup(self):
        self.config = tc.CONF
        self.recipe = pakit.recipe.RDB.get('ag')

    def teardown(self):
        RemoveTask(self.recipe).run()
        try:
            os.remove(pakit.conf.IDB.filename)
        except OSError:
            pass
        try:
            self.recipe.repo.clean()
        except PakitCmdError:
            pass


class DummyTask(Task):
    def run(self):
        pass


class TestTask(TestTaskBase):
    def test__str__(self):
        task = DummyTask()
        print(task)
        assert str(task) == 'DummyTask'


class TestTaskRecipe(TestTaskBase):
    def test_recipe_object(self):
        assert RecipeTask(self.recipe).recipe is self.recipe

    def test__eq__(self):
        assert InstallTask('ag') == InstallTask('ag')
        assert RemoveTask('ag') != InstallTask('ag')
        assert InstallTask('ag') != InstallTask('vim')

    def test__str__(self):
        expect = 'RecipeTask: ag'
        task = RecipeTask(self.recipe)
        print(task)
        assert expect == str(task)


class TestTaskInstall(TestTaskBase):
    def test_is_not_installed(self):
        InstallTask(self.recipe).run()
        name = self.recipe.name

        paths = pakit.conf.CONFIG.get('pakit.paths')
        build_bin = os.path.join(paths['prefix'], name, 'bin', name)
        link_bin = os.path.join(paths['link'], 'bin', name)
        assert os.path.exists(build_bin)
        assert os.path.exists(link_bin)
        assert os.path.realpath(link_bin) == build_bin

    @mock.patch('pakit.task.USER')
    def test_is_installed(self, mock_log):
        task = InstallTask(self.recipe)
        task.run()
        task.run()
        assert mock_log.info.called


class TestTaskRollback(object):
    def setup(self):
        self.config = tc.CONF
        self.recipe = None

    def teardown(self):
        tc.delete_it(self.recipe.install_dir)
        tc.delete_it(self.recipe.link_dir)
        tc.delete_it(self.recipe.source_dir)
        try:
            self.recipe.repo.clean()
        except PakitCmdError:
            pass
        os.makedirs(self.recipe.link_dir)

    def test_install_build_error(self):
        self.recipe = pakit.recipe.RDB.get('build')
        with pytest.raises(PakitCmdError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.path.exists(self.recipe.source_dir)
        assert os.path.exists(self.recipe.link_dir)

    def test_install_link_error(self):
        self.recipe = pakit.recipe.RDB.get('link')
        with pytest.raises(PakitLinkError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.path.exists(self.recipe.source_dir)
        assert os.path.exists(self.recipe.link_dir)

    def test_install_verify_error(self):
        self.recipe = pakit.recipe.RDB.get('verify')
        with pytest.raises(AssertionError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.path.exists(self.recipe.source_dir)
        assert os.path.exists(self.recipe.link_dir)

    def test_update_rollback_error(self):
        self.recipe = pakit.recipe.RDB.get('update')

        self.recipe.repo = 'stable'
        InstallTask(self.recipe).run()
        expect = 'd7193e13a7f8f9fe9732e1f546a39e45d3925eb3'
        assert pakit.conf.IDB.get(self.recipe.name)['hash'] == expect

        self.recipe.repo = 'unstable'
        UpdateTask(self.recipe).run()
        assert pakit.conf.IDB.get(self.recipe.name)['hash'] == expect
        RemoveTask(self.recipe).run()


class TestTaskRemove(TestTaskBase):
    def test_is_not_installed(self, mock_print):
        RemoveTask(self.recipe).run()
        mock_print.assert_called_with('ag: Not Installed')

    def test_is_installed(self):
        InstallTask(self.recipe).run()
        assert self.recipe.name in pakit.conf.IDB

        RemoveTask(self.recipe).run()
        assert self.recipe.name not in pakit.conf.IDB

        paths = pakit.conf.CONFIG.get('pakit.paths')
        assert os.path.exists(paths['prefix'])
        assert os.path.exists(paths['link'])
        assert os.listdir(paths['link']) == []


class TestTaskUpdate(TestTaskBase):
    def teardown(self):
        super(TestTaskUpdate, self).teardown()
        logging.error(ListInstalled().run())

    def test_is_current(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        assert pakit.conf.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        first_hash = recipe.repo.src_hash

        UpdateTask(recipe).run()
        assert pakit.conf.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        assert first_hash == recipe.repo.src_hash

    def test_is_not_current(self):
        recipe = self.recipe
        old_repo_name = recipe.repo_name

        recipe.repo = 'stable'
        InstallTask(recipe).run()
        expect = 'd7193e13a7f8f9fe9732e1f546a39e45d3925eb3'
        assert pakit.conf.IDB.get(recipe.name)['hash'] == expect

        recipe.repo = 'unstable'
        UpdateTask(recipe).run()
        assert pakit.conf.IDB.get(recipe.name)['hash'] != expect

        recipe.repo = old_repo_name

    def test_save_old_install(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        task = UpdateTask(recipe)
        task.save_old_install()
        assert pakit.conf.IDB.get(recipe.name) is None
        assert not os.path.exists(recipe.install_dir)
        assert os.path.exists(recipe.install_dir + '_bak')

    def test_restore_old_install(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        task = UpdateTask(recipe)
        task.save_old_install()
        task.restore_old_install()
        assert pakit.conf.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        assert os.path.exists(recipe.install_dir)
        assert not os.path.exists(recipe.install_dir + '_bak')
        recipe.verify()


class TestTaskRelink(TestTaskBase):
    def test_relink(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        shutil.rmtree(recipe.link_dir)
        assert not os.path.exists(recipe.link_dir)
        RelinkRecipes().run()
        assert sorted(os.listdir(recipe.link_dir)) == ['bin', 'share']
        assert os.path.islink(os.path.join(recipe.link_dir, 'bin', 'ag'))


class TestTaskQuery(TestTaskBase):
    def test_list_installed(self):
        InstallTask(self.recipe).run()
        task = ListInstalled()
        out = task.run().split('\n')
        assert len(out) == 3
        assert out[-1].find('  ' + self.recipe.name) == 0

    def test_list_installed_short(self, mock_print):
        InstallTask(self.recipe).run()
        ListInstalled(True).run()
        mock_print.assert_called_with('ag')

    def test_list_available(self):
        task = ListAvailable()
        out = task.run().split('\n')
        expect = ['  ' + line for line in pakit.recipe.RDB.names(desc=True)]
        print(expect)
        print(out)
        assert out[0] == 'Available Recipes:'
        assert out[2:] == expect

    def test_list_available_short(self, mock_print):
        ListAvailable(True).run()
        expect = ' '.join(pakit.recipe.RDB.names(desc=False))
        mock_print.assert_called_with(expect)

    def test_search_names(self):
        results = SearchTask(pakit.recipe.RDB.names(), ['doxygen']).run()
        assert results[1:] == ['doxygen']

    def test_search_desc(self):
        ack = pakit.recipe.RDB.get('ack')
        results = SearchTask(pakit.recipe.RDB.names(desc=True),
                             [ack.description]).run()
        assert results[1:] == [str(ack)]

    def test_display_info(self):
        prefix = pakit.task.PREFIX
        results = DisplayTask(self.recipe).run()
        expect = prefix[1:] + prefix.join(self.recipe.info().split('\n'))
        assert results == expect
