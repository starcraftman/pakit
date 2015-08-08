## Final Expected Behaviour

* `wok --install tmux ag`       -- Install several programs
* `wok --update`                -- Update local programs
* `wok --remove tmux            -- Remove program
* `wok --list`                  -- List installed programs
* `wok --available`             -- List ALL available formula
* `wok --search lib`            -- Display matching avilable recipes
* `wok --conf ./a.yml -i ag`    -- Override default config
* 'wok --display vim ag`        -- Display package information

Short opts in order: -i -u -r -l -a -s -c -d

## Configuration

File config by hidden YAML file at `~/.wok.yml`.

The idea is a user can define a dict that overrides default
configuration variables of the build in his config file. Allows flexible recipes.

```yaml
# Default options passed to all recipes self.opts, can be overwridden by specific opts.
defaults:
  build: unstable
paths:
  # Where all builds will go, each under /tmp/wok/builds/recipe.name folder
  prefix: /tmp/wok/builds
  # Where builds will link to, should go on your PATH
  link: /tmp/wok/links
  # Where source code will go
  source: /tmp/wok/src
log:
  enabled: true
  file: /tmp/wok/main.log
# Example of specific options, for recipe in 'ag.py'
# Note that here ag will be built with 'stable' repo instead of default.
ag:
  build: stable
  # These two options will be available in build/verify funcs via self.opts.
  option_1: hello
  option_2: world
```

## Recipe Spec

Work In Progress

Below is an example, taken from formula/ag.py.
Core logic implemented in wok/recipe.py
Aim is to have very short easily written recipes.

Parts of standard recipe:
* desc: A short description.
* homepage: Where the project is hosted.
* repos: A dict of possible source downloaders.
* build(): A function that builds the source selectable by config.
* verify(): A function that returns true iff the build is good.

Example:
```py
from wok import *

class Ag(Recipe):
    def __init__(self):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src
        self.repos = {
            'stable': Git(self.src, tag='0.30.0'),
            'unstable': Git(self.src),
        }

    def build(self):
        self.cmd('./build.sh --prefix {prefix}')
        self.cmd('make install')

    def verify(self):
        lines = self.cmd('{link}/bin/ag --version')
        return lines[0].find('ag version') != -1
```
