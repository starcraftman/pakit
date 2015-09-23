""" Formula for building ack """
import os
import shutil

from pakit import Git, Recipe


class Ack(Recipe):
    """
    Advanced grep tool based on perl
    """
    def __init__(self):
        super(Ack, self).__init__()
        self.src = 'https://github.com/petdance/ack2.git'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='2.14'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('perl Makefile.PL')
        self.cmd('make ack-standalone manifypods')
        ack_bin = os.path.join(self.opts['prefix'], 'bin', 'ack')
        man_dir = os.path.join(self.opts['prefix'], 'share',
                               'man', 'man1')
        for path in [os.path.dirname(ack_bin), man_dir]:
            try:
                os.makedirs(path)
            except OSError:
                pass
        shutil.move(os.path.join(self.opts['source'], 'ack-standalone'),
                    ack_bin)
        shutil.move(os.path.join(self.opts['source'], 'blib', 'man1',
                                 'ack.1p'), man_dir)

    def verify(self):
        lines = self.cmd('./bin/ack --version').output()
        assert lines[0].find('ack') != -1
