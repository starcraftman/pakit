""" Formula for building libjsoncpp """
import os

from pakit import Git, Recipe


class Libjsoncpp(Recipe):
    """
    An open source JSON parser for C++
    """
    def __init__(self):
        super(Libjsoncpp, self).__init__()
        self.src = 'https://github.com/open-source-parsers/jsoncpp'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.10.5'),
            'unstable': Git(self.src, branch='0.y.z'),
        }

    def build(self):
        self.cmd('cmake -DCMAKE_INSTALL_PREFIX={prefix} '
                 '-DCMAKE_BUILD_TYPE=release '
                 '-DJSONCPP_LIB_BUILD_SHARED=ON .')
        self.cmd('make install')

    def verify(self):
        libpath = os.path.join(self.opts['link'], 'lib', 'libjsoncpp.a')
        assert os.path.exists(libpath)
