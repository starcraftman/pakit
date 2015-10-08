""" Formula for building vim """
from pakit import Git, Recipe


class Vim(Recipe):
    """
    The mode based terminal editor for programmers.

    By default built with lua & python 2.x interpreters.
    """
    def __init__(self):
        super(Vim, self).__init__()
        self.src = 'https://github.com/vim/vim.git'
        self.homepage = 'www.vim.org'
        self.repos = {
            'stable': Git(self.src, tag='v7.4.865'),
            'unstable': Git(self.src),
        }
        self.opts = {
            'configure': '--with-features=huge --enable-pythoninterp'
        }

    def build(self):
        self.cmd('./configure --prefix={prefix} {configure}')
        self.cmd('make VIMRUNTIMEDIR={prefix}/share/vim/vim74')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/vim --version').output()
        assert lines[0].find('VIM - Vi') != -1
