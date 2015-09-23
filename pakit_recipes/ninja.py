""" Formula for building ninja """
import os
import re

from pakit import Git, Recipe


class Ninja(Recipe):
    """
    A small build system optimized for speed
    """
    def __init__(self):
        super(Ninja, self).__init__()
        self.src = 'https://github.com/martine/ninja.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='release'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./configure.py --bootstrap')
        bin_dir = os.path.join(self.opts['prefix'], 'bin')
        self.cmd('mkdir -p ' + bin_dir)
        self.cmd('mv ninja ' + bin_dir)

    def verify(self):
        lines = self.cmd('./bin/ninja --version').output()
        matcher = re.match(r'\d\.\d+\.\d+', lines[0])
        assert matcher is not None
