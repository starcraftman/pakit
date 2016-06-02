"""
Common code used to streamline testing.

pytest documentation: http://pytest.org/latest/contents.html

See STAGING_REPO for test bed details.
"""
from __future__ import absolute_import, print_function
import os
import shlex
import shutil
import subprocess

import pakit.conf
from pakit.main import global_init, search_for_config
import pakit.recipe

CONF = None
PAKIT_CONFS = []
TEST_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'pakit.yml')
STAGING_REPO = 'https://github.com/pakit/test_staging'
STAGING = '/tmp/staging'
ARCS = os.path.join(STAGING, 'arcs')
GIT = 'https://github.com/ggreer/the_silver_searcher'
HG = 'https://bitbucket.org/sjl/hg-prompt'
TAR = 'https://github.com/tmux/tmux/releases/download/2.0/tmux-2.0.tar.gz'
TAR_FILE = os.path.join(STAGING, 'tmux.tar.gz')
PATHS = [STAGING]


def env_config_setup():
    """
    Copies config to first position looked, `./.pakit.yml`
    Ensures NO other configuration possibly considered.

    NB: Not covered by tests, essentially just search_for_config
    with some file moves.
    """
    global PAKIT_CONFS
    conf_file = search_for_config(1)
    while conf_file != 1:
        shutil.move(conf_file, conf_file + '_bak')
        PAKIT_CONFS.append(conf_file)
        conf_file = search_for_config(1)

    config_dst = '.pakit.yml'
    shutil.copy(TEST_CONFIG, config_dst)


def env_config_teardown():
    """
    Cleans up test config.
    """
    delete_it('.pakit.yml')

    for conf_file in PAKIT_CONFS:
        shutil.move(conf_file + '_bak', conf_file)


def env_setup():
    '''
    Setup the testing environment.
    '''
    global CONF
    if CONF:
        return CONF

    print('\n-----INIT ENV')
    env_config_setup()
    CONF = global_init(TEST_CONFIG)
    PATHS.append(CONF.get('pakit.log.file'))
    PATHS.extend(list(CONF.get('pakit.paths').values()))

    delete_it(os.path.join(CONF.path_to('link'), 'share'))
    delete_it(STAGING)
    cmd = 'git clone --recursive {0} {1}'.format(STAGING_REPO, STAGING)
    subprocess.call(shlex.split(cmd))

    print('\n-----Test recipes:\n', pakit.recipe.RDB.names())
    print()
    print('\n-----INIT ENV FINISHED')

    return CONF


def env_teardown():
    '''
    Teardown the testing environment.
    '''
    print('\n-----DESTROY ENV')

    if len(PATHS) == 1:
        print('Env setup not completed, check network connection.')
        return

    src_log = [path for path in PATHS if '.log' in path][-1]
    dst_log = os.path.join('/tmp', 'test.log')
    try:
        delete_it(dst_log)
        shutil.move(src_log, dst_log)
    except IOError:
        pass

    env_status()

    for path in PATHS:
        delete_it(path)

    env_config_teardown()
    print('\n-----DESTROY ENV FINISHED')


def env_status():
    """
    Print information about the test bed to check tests aren't
    failing to clean up.

    To see, ensure you use: py.test -s
    """
    folders = [folder for folder
               in os.listdir(os.path.dirname(CONF.path_to('link')))
               if folder.find('cmd') == -1]
    try:
        link_d = os.listdir(CONF.path_to('link'))
    except OSError:
        link_d = 'DOES NOT EXIST'
    try:
        prefix_d = os.listdir(CONF.path_to('prefix'))
    except OSError:
        prefix_d = 'DOES NOT EXIST'
    print('\n')
    print('Environment Summary BEFORE Cleanup')
    print('Paths: ', CONF.get('pakit.paths'))
    print('IDB Entries: ', sorted([key for key, _ in pakit.conf.IDB]))
    print('Contents Root Dir: ', sorted(folders))
    print('Contents Link Dir: ', sorted(link_d))
    print('Contents Prefix Dir: ', sorted(prefix_d))


def delete_it(path):
    """
    File or folder, it is deleted.

    Args:
        path: path to a file or dir
    """
    try:
        shutil.rmtree(path)
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass
