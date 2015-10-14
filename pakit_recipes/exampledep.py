""" Formula for building ag """
from __future__ import print_function

from pakit import Dummy, Recipe


class Exampledep(Recipe):
    """
    Dummy recipe, does nothing but illustrate recipe dependency.
    """
    def __init__(self):
        super(Exampledep, self).__init__()
        self.src = 'https://github.com/ggreer/the_silver_searcher.git'
        self.homepage = self.src
        self.repos = {
            'stable': Dummy(),
        }
        self.repos['unstable'] = self.repos['stable']

    def build(self):
        print('Nothing to build.')

    def verify(self):
        print('Nothing to verify.')
