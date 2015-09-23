""" Formula for building p7zip """
from pakit import Archive, Recipe


class P7zip(Recipe):
    """
    The open source command-line implementation of 7-Zip
    """
    def __init__(self):
        super(P7zip, self).__init__()
        self.homepage = 'http://p7zip.sourceforge.net'
        self.repos = {
            'stable': Archive('http://sourceforge.net/projects/p7zip/files/'
                              'p7zip/9.38.1/p7zip_9.38.1_src_all.tar.bz2/'
                              'download',
                              hash='fd5019109c9a1bf34ad3257d37a6853eae8151'
                              'ff50345f0a3ffba7d8c5fdb995')
        }

    def build(self):
        self.cmd('cp -f makefile.linux_any_cpu makefile.machine')
        self.cmd('make 7z 7za 7zr')
        self.cmd('rm -rf DOC')
        self.cmd('make DEST_HOME={prefix} install')
        self.cmd('mv {prefix}/man {prefix}/share')

    def verify(self):
        lines = self.cmd('./bin/7z --help').output()
        assert lines[2].find('p7zip Version') != -1
