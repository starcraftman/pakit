""" Formula for building exampledep """
from __future__ import print_function

from pakit import Dummy, Recipe


class Exampledep(Recipe):
    """
    Dummy recipe, does nothing but illustrate recipe dependency.
    """
    def __init__(self):
        super(Exampledep, self).__init__()
        self.homepage = 'Dummy Recipe'
        repo = Dummy()
        self.repos = {
            'stable': repo,
            'unstable': repo,
        }

    def build(self):
        print('Nothing to build.')

    def verify(self):
        print('Nothing to verify.')
