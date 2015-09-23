""" Formula for building ag """
import os

from pakit import Git, Recipe


class Vimpager(Recipe):
    """
    Use vim as a command line pager
    """
    def __init__(self):
        super(Vimpager, self).__init__()
        self.src = 'https://github.com/rkitover/vimpager'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='2.06'),
            'unstable': Git(self.src),
        }

    # TODO: Depends on `pandoc`
    def build(self):
        self.cmd('make all')
        self.cmd('make PREFIX={prefix} install')

    def verify(self):
        # TODO: Better verify
        pager_bin = os.path.join(self.opts['prefix'], 'bin', 'vimpager')
        assert os.path.exists(pager_bin)
