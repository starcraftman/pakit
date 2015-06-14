from wok import Recipe

class Ag(Plan):
    """ Formula to build latest ag from source. """
    def __init__(self):
        super(Ag, self).__init__(self)
        self._desc = 'Grep like tool sped up with parallelism.'
        self._src = 'https://github.com/ggreer/the_silver_searcher.git'
        self._homepage = 'https://github.com/ggreer/the_silver_searcher'

    def build(self):
        self.com('./build.sh --prefix')
        self.com('make install')

    def verify(self):
        self.com('ctags --version')
