""" Formula for building ag """
from pakit import Git, Recipe


class Ag(Recipe):
    """
    Grep like tool optimized for speed
    """
    def __init__(self):
        super(Ag, self).__init__()
        self.src = 'https://github.com/ggreer/the_silver_searcher.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.31.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/ag --version').output()
        assert lines[0].find('ag version') != -1
