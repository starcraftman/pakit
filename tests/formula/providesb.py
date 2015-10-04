""" Formula that requires no other recipe. """
from pakit import Dummy, Recipe


class Providesb(Recipe):
    """
    Dummy recipe does nothing special but have dependency.
    """
    def __init__(self):
        super(Providesb, self).__init__()
        self.homepage = 'dummy'
        self.repos = {
            'stable': Dummy()
        }

    def build(self):
        pass

    def verify(self):
        pass
