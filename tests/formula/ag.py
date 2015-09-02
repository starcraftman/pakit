""" Formula for building ag """
import os

from pakit import Git, Recipe
import tests.common as tc


class Ag(Recipe):
    """ Grep like tool optimized for speed """
    def __init__(self):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed'
        self.src = os.path.join(tc.STAGING, 'git')
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/ag --version')
        assert lines[0].find('ag version') != -1
