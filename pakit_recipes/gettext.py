""" Formula for building autopoint & gettext """
import os

from pakit import Archive, Git, Recipe


class Gettext(Recipe):
    """
    Autopoint and the gettext library.
    """
    def __init__(self):
        super(Gettext, self).__init__()
        self.homepage = 'https://www.gnu.org/software/gettext'
        self.repos = {
            'stable': Archive('http://ftp.gnu.org/pub/gnu/gettext/'
                              'gettext-0.19.6.tar.gz',
                              hash='ed4b4c19bd3a3034eb6769500a3592ff616759'
                              'ef43cf30586dbb7a17c9dd695d'),
            'unstable': Git('git://git.savannah.gnu.org/gettext.git'),
        }
        # TODO: No gperf recipe yet, required for unstable
        # self.requires = ['gperf']

    def build(self):
        if os.path.exists('autogen.sh'):
            # self.cmd('./autogen.sh')
            raise Exception('Cannot build unstable version yet.')
        self.cmd('./configure --prefix={prefix}')
        self.cmd('make')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('autopoint --version').output()
        assert lines[0].find('autopoint (GNU gettext-tools)') != -1
