from wok import Recipe

class Ag(Recipe):
    def __init__(self):
        super(Ag, self).__init__(self)
        self._desc = 'Grep like tool sped up with parallelism.'
        self._src = 'https://github.com/ggreer/the_silver_searcher.git'
        self._homepage = 'https://github.com/ggreer/the_silver_searcher'

    def build(self):
        self.cmd('./build.sh --prefix')
        self.cmd('make install')

    def verify(self):
        self.cmd('ctags --version')
