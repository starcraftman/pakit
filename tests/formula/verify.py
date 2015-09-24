""" Formula that always errors on verify """
import os

from pakit import Git, Recipe
import tests.common as tc


class Verify(Recipe):
    """
    Formula that always errors on verify
    """
    def __init__(self):
        super(Verify, self).__init__()
        self.src = os.path.join(tc.STAGING, 'git')
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.31.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        assert False
