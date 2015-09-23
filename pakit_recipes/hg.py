""" Formula for building hg """
from pakit import Archive, Recipe
from pakit import Hg as HgRepo


class Hg(Recipe):
    """
    The mercurial distributed version control system
    """
    def __init__(self):
        super(Hg, self).__init__()
        self.homepage = 'https://mercurial.selenic.com'
        self.repos = {
            'stable': Archive('http://mercurial.selenic.com/release/'
                              'mercurial-3.5.1.tar.gz',
                              hash='997da45da303e399678c5bccd7be39b0fabf29'
                              'c7e02fd3c8751c2ff88c8a259d'),
            'unstable': HgRepo('https://selenic.com/hg', branch='stable')
        }

    def build(self):
        self.cmd('make all')
        self.cmd('make PREFIX={prefix} install')

    def verify(self):
        lines = self.cmd('./bin/hg --version').output()
        assert lines[0].find('Mercurial Distributed SCM') != -1
