""" Formula for building autoconf """
from pakit import Archive, Recipe


class Autoconf(Recipe):
    """
    Generate shell scripts to configure source code
    """
    def __init__(self):
        super(Autoconf, self).__init__()
        self.homepage = 'https://www.gnu.org/software/autoconf/autoconf.html'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/autoconf/'
                              'autoconf-2.69.tar.gz',
                              hash='954bd69b391edc12d6a4a51a2dd1476543da5c'
                              '6bbf05a95b59dc0dd6fd4c2969'),
        }

    def build(self):
        self.cmd('./configure --prefix {prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('autoconf --version').output()
        assert lines[0].find('autoconf (GNU Autoconf)') != -1
