""" Formula that always errors on build """
from pakit import Git, Recipe
from pakit.exc import PakitCmdError


class Update(Recipe):
    """ Formula that always errors on build """
    def __init__(self):
        super(Update, self).__init__()
        self.desc = 'Grep like tool optimized for speed'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        if self.repo_name == 'unstable':
            raise PakitCmdError
        else:
            self.cmd('./build.sh --prefix {prefix}')
            self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/ag --version')
        assert lines[0].find('ag version') != -1
