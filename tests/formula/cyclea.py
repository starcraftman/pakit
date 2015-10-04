""" Formula that requires cycleb recipe. """
from pakit import Dummy, Recipe


class Cyclea(Recipe):
    """
    Dummy recipe does nothing special but have dependency.
    """
    def __init__(self):
        super(Cyclea, self).__init__()
        self.homepage = 'dummy'
        self.repos = {
            'stable': Dummy()
        }
        self.requires = ['cycleb']

    def build(self):
        pass

    def verify(self):
        pass
