from wok import Recipe, Git

class Ag(Recipe):
    def __init__(self):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed.'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src
        self.unstable = Git(self.src)

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/ag --version')
        return lines[0].find('ag version') != -1
