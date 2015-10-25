""" Formula for building make """
from pakit import Archive, Recipe


class Make(Recipe):
    """
    GNU make, the classic build tool
    """
    def __init__(self):
        super(Make, self).__init__()
        self.homepage = 'https://www.gnu.org/software/make'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/gnu/make/make-4.1.tar.bz2',
                              hash='0bc7613389650ee6a24554b52572a272f73561'
                              '64fd2c4132b0bcf13123e4fca5'),
        }

    def build(self):
        self.cmd('./configure --prefix {prefix}')
        self.cmd('./build.sh')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('make --version').output()
        assert lines[0].find('GNU Make') != -1
