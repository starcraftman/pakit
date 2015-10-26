""" Formula for building autoconf """
from pakit import Archive, Recipe


class Automake(Recipe):
    """
    Automatically generate Makefile.in files
    """
    def __init__(self):
        super(Automake, self).__init__()
        self.homepage = 'https://www.gnu.org/software/automake'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/automake/'
                              'automake-1.15.tar.gz',
                              hash='7946e945a96e28152ba5a6beb0625ca715c6e3'
                              '2ac55f2e353ef54def0c8ed924'),
        }

    def build(self):
        self.cmd('./configure --prefix {prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('automake --version').output()
        assert lines[0].find('automake (GNU automake)') != -1
