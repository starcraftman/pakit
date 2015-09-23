""" Formula for building ctags """
from pakit import Git, Recipe


class Ctags(Recipe):
    """
    A source code indexing tool
    """
    def __init__(self):
        super(Ctags, self).__init__()
        self.src = 'https://github.com/universal-ctags/ctags'
        self.homepage = self.src
        self.repos = {
            # TODO: They don't have a release yet.
            'stable': Git(self.src),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('autoreconf -fiv')
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/ctags --version').output()
        assert lines[0].find('Universal Ctags Development') != -1
