"""
Common code used to streamline testing.

pytest documentation: http://pytest.org/latest/contents.html
"""
from __future__ import absolute_import, print_function

import logging
import os
import shlex
import shutil
import subprocess
try:
    import urllib2 as ulib
except ImportError:
    import urllib.request as ulib  # pylint: disable=E0611,F0401

import pakit.conf
from pakit.main import global_init
from pakit.recipe import RecipeDB

STAGING = '/tmp/staging'
TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'pakit.yml')
ARCS_URL = 'https://github.com/pakit/arc_fmts'
ARCS = os.path.join(STAGING, 'arcs')
GIT = 'https://github.com/ggreer/the_silver_searcher'
HG = 'https://bitbucket.org/sjl/hg-prompt/'
TAR = 'https://github.com/tmux/tmux/releases/download/2.0/tmux-2.0.tar.gz'
TAR_FILE = os.path.join(STAGING, 'tmux.tar.gz')
PATHS = [STAGING]
CONF = None


def env_config_setup():
    """
    Copies config to first position looked, `./.pakit.yml`

    See pakit.main.search_for_config for details.
    """
    config_dst = '.pakit.yml'
    if os.path.exists(config_dst):
        shutil.move(config_dst, config_dst + '_bak')
    shutil.copy(TEST_CONFIG, config_dst)


def env_config_teardown():
    """
    Cleans up test config.
    """
    config_dst = '.pakit.yml'
    delete_it(config_dst)
    if os.path.exists(config_dst + '_bak'):
        shutil.move(config_dst + '_bak', config_dst)


def env_setup():
    '''
    Setup the testing environment.
    '''
    global CONF
    if CONF:
        return CONF

    logging.info('INIT ENV')
    env_config_setup()
    CONF = global_init(TEST_CONFIG)
    PATHS.append(CONF.get('pakit.log.file'))
    PATHS.extend(list(CONF.get('pakit.paths').values()))

    delete_it(STAGING)
    cmds = [
        'git clone --recursive {0} {1}'.format(ARCS_URL, ARCS),
        'git clone --recursive {0} {1}'.format(GIT,
                                               os.path.join(STAGING, 'git')),
        'hg clone {0} {1}'.format(HG, os.path.join(STAGING, 'hg')),
    ]
    for cmd in cmds:
        subprocess.call(shlex.split(cmd))

    resp = ulib.urlopen(TAR)
    with open(TAR_FILE, 'wb') as fout:
        fout.write(resp.read())

    RecipeDB().index(os.path.join(os.path.dirname(TEST_CONFIG), 'formula'))
    logging.info('Test recipes: %s', RecipeDB().names())
    shutil.rmtree(os.path.join(CONF.path_to('link'), 'share'))

    return CONF


def env_teardown():
    '''
    Teardown the testing environment.
    '''
    logging.info('DESTROY ENV')
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
