""" Formula for building zsh """
from pakit import Archive, Git, Recipe


class Zsh(Recipe):
    """ The zshell, a powerful interactive shell """
    def __init__(self):
        super(Zsh, self).__init__()
        self.desc = 'The zshell, a powerful interactive shell'
        self.homepage = 'http://zsh.sourceforge.net/'
        self.repos = {
            'stable': Archive('http://sourceforge.net/projects/zsh/files/'
                              'zsh/5.0.7/zsh-5.0.7.tar.bz2/download',
                              hash='1500191d16af8a71aec4f719a92775a074682096'),
            'unstable': Git('git://git.code.sf.net/p/zsh/code'),
        }

    def build(self):
        self.cmd('./Util/preconfig')
        self.cmd('autoconf')
        self.cmd('./configure --prefix={prefix} --with-tcsetpgrp')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/zsh --version').output()
        assert lines[0].find('zsh') != -1
