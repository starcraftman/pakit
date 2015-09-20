""" Formula for building p7zip """
import os

from pakit import Archive, Recipe


class P7zip(Recipe):
    """ p7zip is the Unix command-line port of 7-Zip """
    def __init__(self):
        super(P7zip, self).__init__()
        self.desc = 'p7zip is the Unix command-line port of 7-Zip'
        self.homepage = 'http://p7zip.sourceforge.net'
        self.repos = {
            'stable': Archive('http://sourceforge.net/projects/p7zip/files/'
                              'p7zip/9.38.1/p7zip_9.38.1_src_all.tar.bz2/'
                              'download',
                              hash='6b1eccf272d8b141a94758f80727ae633568ba69')
        }

    def build(self):
        self.cmd('cp -f makefile.linux_any_cpu makefile.machine')
        self.cmd('make 7z')
        man_dir = os.path.join('share', 'man', 'man1')
        self.cmd('mkdir -p {prefix}/bin {prefix}/' + man_dir)
        self.cmd('cp ./bin/7z {prefix}/bin')
        self.cmd('cp ./man1/7z.1 {prefix}/' + man_dir)

    def verify(self):
        lines = self.cmd('./bin/7z --help').output()
        assert lines[2].find('p7zip Version') != -1
