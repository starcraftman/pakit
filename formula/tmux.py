""" Formula for building tmux """
from pakit import Git, Recipe


class Tmux(Recipe):
    """ A modern screen replacement """
    def __init__(self):
        super(Tmux, self).__init__()
        self.desc = 'The modern screen replacement'
        self.src = 'https://github.com/tmux/tmux'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='2.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('sh autogen.sh')
        self.cmd('./configure --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/tmux -V')
        return lines[0].find('tmux') != -1
