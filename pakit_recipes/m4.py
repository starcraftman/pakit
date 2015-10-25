""" Formula for building m4 """
from pakit import Archive, Recipe


class M4(Recipe):
    """
    The GNU macro processor, translate input files while expanding macros.
    """
    def __init__(self):
        super(M4, self).__init__()
        self.homepage = 'https://www.gnu.org/software/m4/m4.html'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/m4/m4-1.4.17.tar.bz2',
                              hash='8e4e1f963932136ed45dcd5afb0c6e237e96a6'
                              'fcdcd2a2fa6755040859500d70'),
        }

    def build(self):
        self.cmd('./configure --prefix {prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('m4 --version').output()
        assert lines[0].find('m4 (GNU M4)') != -1
