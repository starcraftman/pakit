## Final Expected Behaviour
---------------------------

* Install several packages: `wok --install tmux ag`
* Upgrade packages:         `wok --upgrade tmux ag`
* Remove packages:          `wok --remove tmux`
* List available formula:   `wok --list`
* Search packs:             `wok --search a*`

NB: Upgrade should imply install I think for simplicity. So if tmux insalled but not ag
ag would get installed and tmux would be chedked for upgrade.

## Configuration
----------------

* File config by hidden YAML file at `~/.wok.yml`.

* install_to:   `wok --install ag` will put all ag files under `install_dir/ag`
* link_to:      The single folder you will put on your PATH
* opts:         Allow you to optionally provide flags to the builds

```yaml
install_to: /tmp/wok/builds
link_to:    /tmp/linked
opts:
  - ag:     --enable-module
  - ack:    --build-doc
workers:    4
logging:
  - enabled: True
  - file: /tmp/wok/main.log
```

## Recipe Spec
--------------
WIP: Not finalized yet.

Could be a python class or simple file. Python class allows more flexility without requiring a DSL.
Should provide common helpers to minimize duplication.
Notably, means to specify download method of source (VCS or archive).

Reference:

```py
from wok import Recipe

class Ag(Recipe):
    def __init__(self, install_d):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed.'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src

    def build(self):
        """ Commands get executed INSIDE the source dir. """
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        """ Commands get executed INSIDE the source dir.
            May be more complex ensuring command/lib works/links.
        """
        self.cmd('./build.sh --prefix {prefix}')
        lines = self.cmd('./bin/ag --version', False)
        return lines[0].find('ag version') != -1
```
