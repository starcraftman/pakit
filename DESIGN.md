## Expected Command Line

* `pakit --install tmux ag`       -- Install several programs
* `pakit --update`                -- Update local programs
* `pakit --remove tmux            -- Remove program
* `pakit --list`                  -- List installed programs
* `pakit --available`             -- List ALL available formula
* `pakit --search lib`            -- Display matching avilable recipes
* `pakit --conf ./a.yaml -i ag`   -- Override default config
* 'pakit --display vim ag`        -- Display package information

Short opts in order: -i -u -r -l -a -s -c -d

## Configuration

File config by a YAML file, default at `~/.pakit.yaml`.

```yaml
# Default options passed to all recipes self.opts, can be overwridden by specific opts.
defaults:
  repo: unstable
paths:
  # Where all builds will go, each under /tmp/pakit/builds/recipe.name folder
  prefix: /tmp/pakit/builds
  # Where builds will link to, should go on your PATH
  link: /tmp/pakit/links
  # Where source code will go
  source: /tmp/pakit/src
  # User can define a series of folders with recipes
  recipes:
    - path1
    - path2
log:
  enabled: true
  file: /tmp/pakit/main.log
# Example of specific options, for recipe in 'ag.py'
# Note that here ag will be built with 'stable' repo instead of default.
ag:
  repo: stable
  # These two options will be available in build/verify funcs via self.opts.
  option_1: hello
  option_2: world
```

## Recipe Specification

Work In Progress

Below is an example, taken from pakit_recipes/ag.py.
Core logic implemented in pakit/recipe.py
Aim is to have very short easily written recipes.

Parts of standard recipe:
* desc: A short description.
* homepage: Where the project is hosted.
* repos: A dict of possible source downloaders.
* build(): A function that builds the source selectable by config.
* verify(): A function that uses `assert` statements to verify build.

Example:
```py
""" Formula for building ag """
from pakit import Git, Recipe


class Ag(Recipe):
    """ Grep like tool optimized for speed """
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
        assert lines[0].find('ag version') != -1
```
