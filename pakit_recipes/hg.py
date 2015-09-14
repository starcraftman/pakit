""" Formula for building hg """
from pakit import Archive, Recipe


class Hg(Recipe):
    """ The distributed version control system """
    def __init__(self):
        super(Hg, self).__init__()
        self.desc = 'The distributed version control system'
        self.homepage = 'https://mercurial.selenic.com'
        repo = Archive('http://mercurial.selenic.com/release/mercurial-3.5.1.tar.gz',
                       hash='fbe9c64dd4c065dbc9330aff4533fa1631d75c79')
        self.repos = {
            'stable': repo,
            'unstable': repo,
        }

    def build(self):
        self.cmd('make all')
        self.cmd('make PREFIX={prefix} install')

    def verify(self):
        lines = self.cmd('{link}/bin/hg --version')
        assert lines[0].find('Mercurial Distributed SCM') != -1
