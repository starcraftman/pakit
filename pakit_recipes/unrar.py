""" Formula for building unrar """
import os

from pakit import Archive, Recipe


class Unrar(Recipe):
    """
    Command line program to extract rar files
    """
    def __init__(self):
        super(Unrar, self).__init__()
        self.homepage = 'http://www.rarlab.com'
        self.repos = {
            'stable': Archive('http://www.rarlab.com/rar/'
                              'unrarsrc-5.3.4.tar.gz',
                              filename='unrarsrc.tar.gz',
                              hash='ce4767b8532f0866c609ec99a0b4d21a2f6cb8'
                              'a786b15092ddf608ec4904b874')
        }

    def build(self):
        self.cmd('make unrar')
        self.cmd('make DESTDIR={prefix} install')

    def verify(self):
        # TODO: Weak verify. Need to make helper functions to facilitate
        # verifying in some temp area that always gets cleaned.
        assert os.path.exists(os.path.join(self.opts['link'], 'bin', 'unrar'))
