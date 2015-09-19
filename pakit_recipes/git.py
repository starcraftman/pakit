""" Formula for building git """
from pakit import Archive, Recipe
from pakit import Git as GitRepo


class Git(Recipe):
    """ The version control system """
    def __init__(self):
        super(Git, self).__init__()
        self.desc = 'The version control system'
        self.homepage = 'https://git-scm.com'
        self.repos = {
            'stable': Archive('https://www.kernel.org/pub/software/scm/git/'
                              'git-2.5.2.tar.xz',
                              hash='5078512c7dba1db2d98814c1abe7550dc18507c9'),
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
