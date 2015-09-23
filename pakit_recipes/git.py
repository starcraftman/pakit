""" Formula for building git """
from pakit import Archive, Recipe
from pakit import Git as GitRepo


class Git(Recipe):
    """
    The git distributed version control system
    """
    def __init__(self):
        super(Git, self).__init__()
        self.homepage = 'https://git-scm.com'
        self.repos = {
            'stable': Archive('https://www.kernel.org/pub/software/scm/git/'
                              'git-2.5.2.tar.xz',
                              hash='4b4760a90ede51accee703bd6815f1f79afef6'
                              '8670acdcf3ea31dcc846a40c9b'),
            'unstable': GitRepo('https://github.com/git/git'),
        }

    def build(self):
        self.cmd('make configure')
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/git --version').output()
        assert lines[0].find('git version') != -1
