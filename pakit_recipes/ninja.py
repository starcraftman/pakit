""" Formula for building ninja """
import os
import re

from pakit import Git, Recipe


class Ninja(Recipe):
    """ A small build system optimized for speed """
    def __init__(self):
        super(Ninja, self).__init__()
        self.desc = 'A small build system optimized for speed'
        self.src = 'https://github.com/martine/ninja.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='release'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./configure.py --bootstrap')
        os.renames('{source}/ninja'.format(**self.opts),
                   '{prefix}/bin/ninja'.format(**self.opts))

    def verify(self):
        lines = self.cmd('./bin/ninja --version').output()
        matcher = re.match(r'\d\.\d+\.\d+', lines[0])
        assert matcher is not None
