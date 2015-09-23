""" Formula for building tmux """
from pakit import Archive, Git, Recipe
import os


class Tmux(Recipe):
    """
    A modern GNU screen replacement
    """
    def __init__(self):
        super(Tmux, self).__init__()
        self.src = 'https://github.com/tmux/tmux'
        self.homepage = self.src
        self.repos = {
            'stable': Archive('https://github.com/tmux/tmux/releases/download'
                              '/2.0/tmux-2.0.tar.gz',
                              hash='795f4b4446b0ea968b9201c25e8c1ef8a6ade7'
                              '10ebca4657dd879c35916ad362'),
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
