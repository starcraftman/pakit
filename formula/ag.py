from wok import Recipe

class Ag(Recipe):
    def __init__(self):
        super(Ag, self).__init__()
        self._desc = 'Grep like tool optimized for speed.'
        self._src = 'https://github.com/ggreer/the_silver_searcher'
        self._homepage = self._src

    def build(self):
        self.cmd('./build.sh --prefix {0}'.format(self.idir()), self.sdir())
        self.cmd('make install', self.sdir())

    def verify(self):
        lines = self.cmd('./bin/ag --version', self.idir())
        return lines[0].find('ag version') != -1
