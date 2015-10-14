""" Formula for building example """
from __future__ import print_function
from pakit import Git, Recipe
import os


class Example(Recipe):
    """
    Example recipe. This line should be a short description.

    This is a longer description.
    It can be of any length.

    Have breaks in text.
    It will be presented as 'More Information' when displaying a Recipe.
    For instance `pakit --display example`.
    """
    def __init__(self):
        super(Example, self).__init__()
        self.src = 'https://github.com/ggreer/the_silver_searcher.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }
        self.requires = ['exampledep']

    def log(self, msg):  # pylint: disable=R0201
        """
        Simple method prints message followed by current working directory.

        You can add any method you want to Recipe so long as pakit's
        conventions are followed. I currently do no checking  to ensure
        they are.
        """
        print(msg, 'the working directory is', os.getcwd())

    def pre_build(self):
        """
        Optional method, will execute before build().
        The working directory will be the source code directory.
        """
        self.log('Before build()')

    def build(self):
        """
        Required method, build the program and install it into the install_dir.
        The working directory will be the source code directory.

        """
        self.log('build()')

    def post_build(self):
        """
        Optional method, will execute after build().
        The working directory will be the source code directory.
        """
        self.log('After build()')

    def pre_verify(self):
        """
        Will execute before build().
        """
        self.log('Before verify()')

    def verify(self):
        self.log('verify()')

    def post_verify(self):
        """
        Will execute after verify().
        """
        self.log('After verify()')
