""" Formula for building tmux """
from pakit import Archive, Git, Recipe
import os


class Tmux(Recipe):
    """ A modern screen replacement """
    def __init__(self):
        super(Tmux, self).__init__()
        self.desc = 'The modern screen replacement'
        self.src = 'https://github.com/tmux/tmux'
        self.homepage = self.src
        self.repos = {
            'stable': Archive('https://github.com/tmux/tmux/releases/download'
                              '/2.0/tmux-2.0.tar.gz',
                              hash='977871e7433fe054928d86477382bd5f6794dc3d'),
            'unstable': Git(self.src),
        }

    def build(self):
        if os.path.exists(os.path.join(self.opts['source'], 'autogen.sh')):
            self.cmd('sh autogen.sh')

        self.cmd('./configure --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/tmux -V').output()
        assert lines[0].find('tmux') != -1
