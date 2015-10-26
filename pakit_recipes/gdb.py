""" Formula for building gdb """
from pakit import Archive, Recipe


class Gdb(Recipe):
    """
    The GNU debugger
    """
    def __init__(self):
        super(Gdb, self).__init__()
        self.homepage = 'https://www.gnu.org/software/gdb'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/gdb/gdb-7.10.tar.xz',
                              hash='7ebdaa44f9786ce0c142da4e36797d2020c55f'
                              'a091905ac5af1846b5756208a8'),
        }

    def build(self):
        self.cmd('./configure --prefix {prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('gdb --version').output()
        assert lines[0].find('GNU gdb') != -1
