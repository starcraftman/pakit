""" Formula for building doxygen """
import glob
import os
import re
import shutil

from pakit import Git, Recipe
from pakit.exc import PakitCmdError


class Doxygen(Recipe):
    """
    The C++ documentation generator
    """
    def __init__(self):
        super(Doxygen, self).__init__()
        self.src = 'https://github.com/doxygen/doxygen.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='Release_1_8_10'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('cmake .')
        self.cmd('make')
        try:
            man_dir = os.path.join(self.opts['prefix'], 'share', 'man', 'man1')
            os.makedirs(man_dir)
            shutil.move('{source}/bin'.format(**self.opts),
                        self.opts['prefix'])
            for path in glob.glob(os.path.join(self.opts['source'],
                                               'doc', '*.1')):
                shutil.move(path, man_dir)
        except (OSError, IOError) as exc:
            raise PakitCmdError(exc)

    def verify(self):
        lines = self.cmd('./bin/doxygen --version').output()
        matcher = re.match(r'\d\.\d+\.\d+', lines[0])
        assert matcher is not None
