"""
Test pakit.task
"""
from __future__ import absolute_import, print_function

import glob
import logging
import mock
import os
import pytest
import sys

from pakit.exc import PakitCmdError, PakitLinkError
from pakit.recipe import RecipeDB
from pakit.task import (
    subseq_match, substring_match, walk_and_link, walk_and_unlink,
    Task, RecipeTask, InstallTask, RemoveTask, UpdateTask, DisplayTask,
    ListInstalled, ListAvailable, SearchTask
)
import pakit.task
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


class TestLinking(object):
    def setup(self):
        config = tc.env_setup()
        self.src = config.get('paths.prefix')
        self.dst = config.get('paths.link')
        self.teardown()

        self.subdir = os.path.join(self.src, 'subdir')
        os.makedirs(self.subdir)

        self.fnames = [os.path.join(self.src, 'file' + str(num))
                       for num in range(0, 6)]
        self.fnames += [os.path.join(self.subdir, 'file' + str(num))
                        for num in range(0, 4)]
        self.dst_fnames = [fname.replace(self.src, self.dst)
                           for fname in self.fnames]
        for fname in self.fnames:
            with open(fname, 'wb') as fout:
                fout.write('dummy'.encode())

    def teardown(self):
        tc.delete_it(self.src)
        tc.delete_it(self.dst)
        for path in [self.src, self.dst]:
            try:
                os.makedirs(path)
            except OSError:
                pass

    def test_walk_and_link_works(self):
        walk_and_link(self.src, self.dst)
        for fname in self.dst_fnames:
            assert os.path.islink(fname)
            assert os.readlink(fname) == fname.replace(self.dst, self.src)

    def test_walk_and_link_raises(self):
        walk_and_link(self.src, self.dst)
        with pytest.raises(PakitLinkError):
            walk_and_link(self.src, self.dst)

    def test_walk_and_unlink(self):
        walk_and_link(self.src, self.dst)
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)

    def test_walk_and_unlink_missing(self):
        walk_and_link(self.src, self.dst)
        os.remove(self.dst_fnames[0])
        walk_and_unlink(self.src, self.dst)
        for fname in self.dst_fnames:
            assert not os.path.exists(fname)
        assert not os.path.exists(self.subdir.replace(self.src, self.dst))
        for fname in self.fnames:
            assert os.path.exists(fname)


class TestTaskBase(object):
    """ Shared setup, most task tests will want this. """
    def setup(self):
        self.config = tc.env_setup()
        self.recipe = RecipeDB().get('ag')

    def teardown(self):
        RemoveTask(self.recipe).run()
        try:
            os.remove(os.path.join(os.path.dirname(self.recipe.install_dir),
                                   'installed.yaml'))
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
        expect = 'DummyTask: Config File ' + self.config.filename
        task = DummyTask()
        print(task)
        assert str(task) == expect


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
        task = InstallTask(self.recipe)
        task.run()
        name = self.recipe.name
        build_bin = os.path.join(task.path('prefix'), name, 'bin', name)
        link_bin = os.path.join(task.path('link'), 'bin', name)
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
        self.config = tc.env_setup()
        self.recipe = None

    def teardown(self):
        tc.delete_it(self.recipe.install_dir)
        tc.delete_it(self.recipe.link_dir)
        tc.delete_it(self.recipe.source_dir)
        try:
            self.recipe.repo.clean()
        except PakitCmdError:
            pass

    def test_install_build_error(self):
        self.recipe = RecipeDB().get('build')
        with pytest.raises(PakitCmdError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.listdir(os.path.dirname(self.recipe.source_dir)) == []

    def test_install_link_error(self):
        self.recipe = RecipeDB().get('link')
        with pytest.raises(PakitLinkError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.listdir(os.path.dirname(self.recipe.source_dir)) == []
        assert not os.path.exists(self.recipe.link_dir)

    def test_install_verify_error(self):
        self.recipe = RecipeDB().get('verify')
        with pytest.raises(AssertionError):
            InstallTask(self.recipe).run()
        assert os.listdir(os.path.dirname(self.recipe.install_dir)) == []
        assert os.listdir(os.path.dirname(self.recipe.source_dir)) == []
        assert not os.path.exists(self.recipe.link_dir)

    def test_update_rollback_error(self):
        self.recipe = RecipeDB().get('update')

        self.recipe.repo = 'stable'
        InstallTask(self.recipe).run()
        expect = 'c81622c5c5313c05eab2da3b5eca6c118b74369e'
        assert pakit.task.IDB.get(self.recipe.name)['hash'] == expect

        self.recipe.repo = 'unstable'
        UpdateTask(self.recipe).run()
        assert pakit.task.IDB.get(self.recipe.name)['hash'] == expect
        RemoveTask(self.recipe).run()


class TestTaskRemove(TestTaskBase):
    def test_is_not_installed(self):
        if sys.version[0] == '2':
            print_mod = '__builtin__.print'
        else:
            print_mod = 'builtins.print'
        with mock.patch(print_mod) as mock_print:
            task = RemoveTask(self.recipe)
            task.run()
            mock_print.assert_called_with('ag: Not Installed')

    def test_is_installed(self):
        InstallTask(self.recipe).run()
        task = RemoveTask(self.recipe)
        task.run()

        assert os.path.exists(task.path('prefix'))
        globbed = glob.glob(os.path.join(task.path('prefix'), '*'))
        assert globbed == [os.path.join(task.path('prefix'), 'installed.yaml')]
        assert not os.path.exists(task.path('link'))


class TestTaskUpdate(TestTaskBase):
    def teardown(self):
        super(TestTaskUpdate, self).teardown()
        logging.error(ListInstalled().run())

    def test_is_current(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        assert pakit.task.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        first_hash = recipe.repo.src_hash

        UpdateTask(recipe).run()
        assert pakit.task.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        assert first_hash == recipe.repo.src_hash

    def test_is_not_current(self):
        recipe = self.recipe
        old_repo_name = recipe.repo_name

        recipe.repo = 'stable'
        InstallTask(recipe).run()
        expect = 'c81622c5c5313c05eab2da3b5eca6c118b74369e'
        assert pakit.task.IDB.get(recipe.name)['hash'] == expect

        recipe.repo = 'unstable'
        UpdateTask(recipe).run()
        assert pakit.task.IDB.get(recipe.name)['hash'] != expect

        recipe.repo = old_repo_name

    def test_save_old_install(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        task = UpdateTask(recipe)
        task.save_old_install()
        assert pakit.task.IDB.get(recipe.name) is None
        assert not os.path.exists(recipe.install_dir)
        assert os.path.exists(recipe.install_dir + '_bak')

    def test_restore_old_install(self):
        recipe = self.recipe
        InstallTask(recipe).run()
        task = UpdateTask(recipe)
        task.save_old_install()
        task.restore_old_install()
        assert pakit.task.IDB.get(recipe.name)['hash'] == recipe.repo.src_hash
        assert os.path.exists(recipe.install_dir)
        assert not os.path.exists(recipe.install_dir + '_bak')
        recipe.verify()


class TestTaskQuery(TestTaskBase):
    def test_list_installed(self):
        InstallTask(self.recipe).run()
        task = ListInstalled()
        out = task.run().split('\n')
        assert len(out) == 3
        assert out[-1].find('  ' + self.recipe.name) == 0

    def test_list_installed_short(self):
        if sys.version[0] == '2':
            print_mod = '__builtin__.print'
        else:
            print_mod = 'builtins.print'
        with mock.patch(print_mod) as mock_print:
            InstallTask(self.recipe).run()
            ListInstalled(True).run()
            mock_print.assert_called_with('ag')

    def test_list_available(self):
        task = ListAvailable()
        out = task.run().split('\n')
        expect = ['  ' + line for line in RecipeDB().names(desc=True)]
        print(expect)
        print(out)
        assert out[0] == 'Available Recipes:'
        assert out[2:] == expect

    def test_list_available_short(self):
        if sys.version[0] == '2':
            print_mod = '__builtin__.print'
        else:
            print_mod = 'builtins.print'
        with mock.patch(print_mod) as mock_print:
            ListAvailable(True).run()
            expect = ' '.join(RecipeDB().names(desc=False))
            mock_print.assert_called_with(expect)

    def test_search_names(self):
        results = SearchTask(RecipeDB().names(), ['doxygen']).run()
        assert results[1:] == ['doxygen']

    def test_search_desc(self):
        ack = RecipeDB().get('ack')
        results = SearchTask(RecipeDB().names(desc=True),
                             [ack.description]).run()
        assert results[1:] == [str(ack)]

    def test_display_info(self):
        prefix = pakit.task.PREFIX
        results = DisplayTask(self.recipe).run()
        expect = prefix[1:] + prefix.join(self.recipe.info().split('\n'))
        assert results == expect
