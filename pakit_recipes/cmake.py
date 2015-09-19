""" Formula for building cmake """
from pakit import Archive, Git, Recipe


class Cmake(Recipe):
    """ A cross-platform build tool for C++ """
    def __init__(self):
        super(Cmake, self).__init__()
        self.desc = 'A cross-platform build tool for C++'
        self.homepage = 'www.cmake.org'
        self.repos = {
            'stable': Archive('http://www.cmake.org/files/v3.3/'
                              'cmake-3.3.1.tar.gz',
                              hash='799aff559e9f330fefc60e6509f1d025fc3d9c8c'),
            'unstable': Git('git://cmake.org/cmake.git '),
        }

    def build(self):
        self.cmd('./bootstrap --prefix={prefix} --mandir=share/man '
                 '--sphinx-html --sphinx-man')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/cmake --version').output()
        assert lines[0].find('cmake version') != -1
