""" Formula that requires cyclea recipe. """
from pakit import Dummy, Recipe


class Cycleb(Recipe):
    """
    Dummy recipe does nothing special but have dependency.
    """
    def __init__(self):
        super(Cycleb, self).__init__()
        self.homepage = 'dummy'
        self.repos = {
            'stable': Dummy()
        }
        self.requires = ['cyclea']

    def build(self):
        pass

    def verify(self):
        pass
