## Final Expected Behaviour
---------------------------

* Install several packages: `wok --install tmux ag`
* Update local packages:    `wok --update`
* Update recipes:           `wok --recipes`
* Remove packages:          `wok --remove tmux`
* List available formula:   `wok --list`
* Search packs:             `wok --search a*`
* Override default config:  `wok --conf ./a.yml -i ag`

shtopts: -i -u -c -r -l -s

## Configuration
----------------

* File config by hidden YAML file at `~/.wok.yml`.

* install_to:   `wok --install ag` will put all ag files under `install_dir/ag`
* link_to:      The single folder you will put on your PATH
* threads:      Max number builds running
* opts:         Allow you to optionally provide flags to the builds

```yaml
install_to: /tmp/wok/builds
link_to:    /tmp/linked
threads:    4
logging:
  - on:     True
  - file:   /tmp/wok/main.log
opts:
  - ag:     --enable-module
```

## Recipe Spec
--------------
WIP: Not finalized yet.

Could be a python class or simple file. Python class allows more flexility without requiring a DSL.
Should provide common helpers to minimize duplication.
Notably, means to specify download method of source (VCS or archive).

Example:
```py
from wok import Recipe, cmd

class Ag(Recipe):
    def __init__(self, install_d):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed.'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src

    def build(self):
        """ Commands get executed INSIDE the source dir. """
        cmd('./build.sh --prefix {prefix}')
        cmd('make install')

    def verify(self):
        """ Commands get executed INSIDE the source dir.
            May be more complex ensuring command/lib works/links.
        """
        cmd('./build.sh --prefix {prefix}')
        lines = self.cmd('./bin/ag --version', False)
        return lines[0].find('ag version') != -1
```
