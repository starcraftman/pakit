""" Formula for building xz utils """
from pakit import Git, Recipe


class Xz(Recipe):
    """
    The xz compression utilities.
    """
    def __init__(self):
        super(Xz, self).__init__()
        self.src = 'http://git.tukaani.org/xz.git'
        self.homepage = 'http://tukaani.org/xz/'
        self.repos = {
            'stable': Git(self.src, tag='v5.2.2'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('autoreconf -fiv')
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('xz --version').output()
        assert lines[0].find('xz (XZ Utils)') != -1
