# This docstring is not used by pakit, by convention they are usually similar
""" Formula for building example """

# All Recipes must be usable on python 2.7+, use future print if needed
from __future__ import print_function

# Pakit provides convenience classes, full list available with `pydoc pakit`
# Import only those you need.
from pakit import Git, Recipe

# Feel free to use standard libs provided with python 2.7
# avoid python 3 specific dependencies
import os


# This recipe should be in file 'example.py'
# It can be referenced by pakit commands as 'example'
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
        # Required
        super(Example, self).__init__()
        # Extra attributes are ignored by pakit
        self.src = 'https://github.com/ggreer/the_silver_searcher.git'
        # The homepage of the project, should be information for users
        self.homepage = self.src
        # A dictionary of Fetchable classes, used to get the source code
        # By convention, should always have 'stable' and 'unstable' keys
        # 'stable' -> point to stable release of source code
        # 'unstable' -> point to a more recent version, like branch of code
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }
        # OPTIONAL: If present, this Recipe requires listed Recipes to be
        #           installed before it can be.
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
        OPTIONAL: Will be called BEFORE build().

        When called, the working directory will be set to the source code.

        Possible Use Case: Patching source before build().
        """
        self.log('Before build()')

    def build(self):
        """
        MANDATORY

        When called, the working directory will be set to the source code.
        Steps should be taken to build and install the program.
        Issue system commands using self.cmd.
        For usage, see 'pydoc pakit.recipe.cmd` for details.
        """
        self.log('build()')

    def post_build(self):
        """
        OPTIONAL: Will be called AFTER build().

        When called, the working directory will be set to the source code.

        Possible Use Case: Patching files after installed.
        """
        self.log('After build()')

    def pre_verify(self):
        """
        OPTIONAL: Will be called BEFORE verify().

        When called, the working directory will be set to a temporary
        directory created by pakit.
        Your program binaries will be available  at the front of $PATH.
        You may do anything in the temp directory so long as permission
        to delete the files/folder are not removed.

        Possible Use Case: Fetch some remote file to test against.
        """
        self.log('Before verify()')

    def verify(self):
        """
        MANDATORY

        When called, the working directory will be set to a temporary
        directory created by pakit.
        Your program binaries will be available  at the front of $PATH.
        You may do anything in the temp directory so long as permission
        to delete the files/folder are not removed.

        You should execute Commands with self.cmd and verify the output.
        Use 'assert' statements to ensure the build is good.
        """
        self.log('verify()')
        assert True

    def post_verify(self):
        """
        OPTIONAL: Will be called AFTER verify().

        When called, the working directory will be set to a temporary
        directory created by pakit.
        Your program binaries will be available  at the front of $PATH.
        You may do anything in the temp directory so long as permission
        to delete the files/folder are not removed.

        Possible Use Case: Not yet found.
        """
        self.log('After verify()')
