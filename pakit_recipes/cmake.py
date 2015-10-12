""" Formula for building cmake """
from pakit import Archive, Git, Recipe


class Cmake(Recipe):
    """
    A cross-platform build tool for C++
    """
    def __init__(self):
        super(Cmake, self).__init__()
        self.homepage = 'www.cmake.org'
        self.repos = {
            'stable': Archive('http://www.cmake.org/files/v3.3/'
                              'cmake-3.3.2.tar.gz',
                              hash='e75a178d6ebf182b048ebfe6e0657c49f0dc10'
                              '9779170bad7ffcb17463f2fc22'),
            'unstable': Git('git://cmake.org/cmake.git '),
        }
        self.opts = {
            'bootstrap': '--sphinx-html --sphinx-man'
        }

    def build(self):
        self.cmd('./bootstrap --prefix={prefix} --mandir=share/man '
                 '{bootstrap}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('cmake --version').output()
        assert lines[0].find('cmake version') != -1
