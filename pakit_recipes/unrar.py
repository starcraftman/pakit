""" Formula for building unrar """
import os

from pakit import Archive, Recipe


class Unrar(Recipe):
    """ Utility to extract rar files """
    def __init__(self):
        super(Unrar, self).__init__()
        self.desc = 'Utility to extract rar files'
        self.homepage = 'http://www.rarlab.com'
        self.repos = {
            'stable': Archive('http://www.rarlab.com/rar/'
                              'unrarsrc-5.3.4.tar.gz',
                              filename='unrarsrc.tar.gz',
                              hash='67a744b08c2ecf1d893bf0b0a7a51d486affb9a2')
        }

    def build(self):
        self.cmd('make unrar')
        self.cmd('make DESTDIR={prefix} install')

    def verify(self):
        # TODO: Weak verify. Need to make helper functions to facilitate
        # verifying in some temp area that always gets cleaned.
        assert os.path.exists(os.path.join(self.opts['link'], 'bin', 'unrar'))
