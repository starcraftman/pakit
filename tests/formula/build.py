""" Formula that always errors on build """
import os

from pakit import Git, Recipe
from pakit.exc import PakitCmdError
import tests.common as tc


class Build(Recipe):
    """
    Formula that always errors on build
    """
    def __init__(self):
        super(Build, self).__init__()
        self.src = os.path.join(tc.STAGING, 'git')
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.31.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')
        raise PakitCmdError

    def verify(self):
        lines = self.cmd('ag --version').output()
        assert lines[0].find('ag version') != -1
