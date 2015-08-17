""" Formula for building vim """
from pakit import Git, Recipe


class Vim(Recipe):
    """ The classic mode based terminal editor """
    def __init__(self):
        super(Vim, self).__init__()
        self.desc = 'The classic mode based terminal editor'
        self.src = 'https://github.com/vim/vim'
        self.homepage = 'www.vim.org'
        self.repos = {
            'stable': Git(self.src),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./configure --prefix={prefix} --with-features=huge '
                 '--enable-cscope --enable-multibyte --enable-luainterp '
                 '--enable-pythoninterp')
        self.cmd('make VIMRUNTIMEDIR={prefix}/share/vim/vim74')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/vim --version')
        return lines[0].find('VIM - Vi') != -1
