""" Formula for building tar """
import os

from pakit import Archive, Git, Recipe


class Tar(Recipe):
    """
    The GNU tar utility.
    """
    def __init__(self):
        super(Tar, self).__init__()
        self.homepage = 'https://www.gnu.org/software/tar'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/tar/tar-1.28.tar.bz2',
                              hash='60e4bfe0602fef34cd908d91cf638e17eeb093'
                              '94d7b98c2487217dc4d3147562'),
            'unstable': Git('git://git.savannah.gnu.org/tar.git'),
        }
        self.requires = ['gettext']

    def build(self):
        if os.path.exists('bootstrap'):
            self.cmd('./bootstrap')
            self.cmd('autoconf')
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('tar --version').output()
        assert lines[0].find('tar (GNU tar)') == 0
