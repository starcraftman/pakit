from wok import Recipe

class Ag(Recipe):
    def __init__(self, install_d):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed.'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src
        self.install_d = install_d

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/ag --version', False)
        return lines[0].find('ag version') != -1
