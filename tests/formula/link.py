""" Formula that always errors on link """
import os

from pakit import Git, Recipe


class Link(Recipe):
    """ Formula that always errors on link """
    def __init__(self):
        super(Link, self).__init__()
        self.desc = 'Grep like tool optimized for speed'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')
        # sabotage linking
        link_path = os.path.join('{link}', 'bin').format(**self.opts)
        os.makedirs(link_path)
        with open(os.path.join(link_path, 'ag'), 'wb') as fout:
            fout.write('dummy'.encode())

    def verify(self):
        lines = self.cmd('{link}/bin/ag --version')
        assert lines[0].find('ag version') != -1
