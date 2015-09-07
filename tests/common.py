"""
Common code used to streamline testing.

pytest documentation: http://pytest.org/latest/contents.html
"""
import atexit
import logging
import os
from os.path import join as pjoin
import shlex
import shutil
import subprocess as sub
try:
    import urllib2 as ulib
except ImportError:
    import urllib.request as ulib  # pylint: disable=E0611,F0401

from pakit.main import global_init
from pakit.recipe import RecipeDB

TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'pakit.yaml')
STAGING = '/tmp/staging'
ARCS = 'https://github.com/pakit/arc_fmts'
GIT = 'https://github.com/ggreer/the_silver_searcher'
HG = 'https://bitbucket.org/sjl/hg-prompt/'
TAR = 'https://github.com/tmux/tmux/releases/download/2.0/tmux-2.0.tar.gz'
CONF = None
PATHS = [STAGING]


def env_setup():
    '''
    Setup the testing environment.
    '''
    global CONF
    if CONF:
        return CONF

    CONF = global_init(TEST_CONFIG)
    logging.info('INIT ENV')
    PATHS.append(CONF.get('log.file'))
    PATHS.extend(list(CONF.get('paths').values()))

    delete_it(STAGING)
    cmds = [
        'git clone --recursive {0} {1}'.format(ARCS, pjoin(STAGING,
                                               'archive')),
        'git clone --recursive {0} {1}'.format(GIT, pjoin(STAGING, 'git')),
        'hg clone {0} {1}'.format(HG, pjoin(STAGING, 'hg')),
    ]
    for cmd in cmds:
        sub.call(shlex.split(cmd))

    resp = ulib.urlopen(TAR)
    with open(pjoin(STAGING, 'tmux.tar.gz'), 'wb') as fout:
        fout.write(resp.read())

    RecipeDB().index(pjoin(os.path.dirname(TEST_CONFIG), 'formula'))
    logging.info('Test recipes: %s', RecipeDB().names())

    atexit.register(env_teardown)

    return CONF


def env_teardown():
    '''
    Teardown the testing environment.
    '''
    logging.info('DESTROY ENV')
    src_log = [path for path in PATHS if '.log' in path][-1]
    dst_log = pjoin('/tmp', 'test.log')
    try:
        delete_it(dst_log)
        shutil.move(src_log, dst_log)
    except IOError:
        pass
    for path in PATHS:
        delete_it(path)


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