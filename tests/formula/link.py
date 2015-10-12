""" Formula that always errors on link """
import os

from pakit import Git, Recipe
import tests.common as tc


class Link(Recipe):
    """
    Formula that always errors on link
    """
    def __init__(self):
        super(Link, self).__init__()
        self.src = os.path.join(tc.STAGING, 'git')
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.31.0'),
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
        lines = self.cmd('ag --version').output()
        assert lines[0].find('ag version') != -1
