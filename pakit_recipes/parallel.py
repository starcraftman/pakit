""" Formula for building parallel """
from pakit import Archive, Recipe


class Parallel(Recipe):
    """ GNU parallel executes shell jobs in parallel """
    def __init__(self):
        super(Parallel, self).__init__()
        self.desc = 'GNU parallel executes shell jobs in parallel'
        self.homepage = 'http://www.gnu.org/software/parallel'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/parallel/'
                              'parallel-20150822.tar.bz2',
                              hash='befa48aac03fbac3f45b3500f2a072d1568eda6a')
        }

    def build(self):
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/parallel --version').output()
        assert lines[0].find('GNU parallel') != -1
