from wok import Recipe

class Vim(Recipe):
    def __init__(self, install_d):
        super(Vim, self).__init__()
        self.desc = 'The classic mode based terminal editor.'
        self.url_src = 'https://github.com/vim/vim'
        self.homepage = self.url_src
        self.install_d = install_d

    def build(self):
        self.cmd('./configure --prefix={prefix} --with-features=huge '
                '--enable-cscope --enable-multibyte --enable-luainterp '
                '--enable-pythoninterp')
        self.cmd('make VIMRUNTIMEDIR={prefix}/share/vim/vim74')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('./bin/vim --version', False)
        return lines[0].find('VIM - Vi') != -1
