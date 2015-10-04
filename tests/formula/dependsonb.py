""" Formula that requires providesb recipe. """
from pakit import Dummy, Recipe


class Dependsonb(Recipe):
    """
    Dummy recipe does nothing special but have dependency.
    """
    def __init__(self):
        super(Dependsonb, self).__init__()
        self.homepage = 'dummy'
        self.repos = {
            'stable': Dummy()
        }
        self.requires = ['providesb']

    def build(self):
        pass

    def verify(self):
        pass
