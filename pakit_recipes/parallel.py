""" Formula for building parallel """
from pakit import Archive, Recipe


class Parallel(Recipe):
    """
    GNU parallel executes shell jobs in parallel
    """
    def __init__(self):
        super(Parallel, self).__init__()
        self.homepage = 'http://www.gnu.org/software/parallel'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/parallel/'
                              'parallel-20150822.tar.bz2',
                              hash='ad9007530d87687160fd8def58721acdac244c'
                              '151b6c007f35068909bb5c47c6')
        }

    def build(self):
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/parallel --version').output()
        assert lines[0].find('GNU parallel') != -1
