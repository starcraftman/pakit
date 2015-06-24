## Final Expected Behaviour

* `wok --install tmux ag`       -- Install several programs
* `wok --update`                -- Update local programs
* `wok --remove tmux            -- Remove program
* `wok --list`                  -- List installed programs
* `wok --available`             -- List available formula
* `wok --search lib`            -- Display matching avilable recipes
* `wok --conf ./a.yml -i ag`    -- Override default config

Short opts in order: -i -u -r -l -a -s -c

## Configuration

File config by hidden YAML file at `~/.wok.yml`.
Most are self-explanitory, except for opts.
The idea is a user can define a dict that overrides default
configuration variables of the build in his config file. Allows flexible recipes.

```yaml
path:
  install:  /tmp/wok/builds
  link:     /tmp/linked
  sources:  /tmp/wok/src
logging:
  on:       True
  file:     /tmp/wok/main.log
opts:
  ag:
    opt1:   --enable-mod1
    opt2:   --enable-mod2
```

## Recipe Spec

Work In Progress

Probably going to be a python class.
Should provide helpers to facilitate common tasks like download/extract archive.
User has choice between stable release & source build.

Example:
```py
from wok import Recipe

class Ag(Recipe):
    def __init__(self, install_d):
        super(Ag, self).__init__()
        self.desc = 'Grep like tool optimized for speed.'
        self.src = 'https://github.com/ggreer/the_silver_searcher'
        self.homepage = self.src

    def release(self):
        """ Download latest stable release. """
        self.tap()

    def tap(self):
        """ Download the source from the tap. """
        git(self.src)

    def build(self):
        """ Commands to build & install program.
            Executed inside the build environment.
        """
        cmd('./build.sh --prefix {prefix}')
        cmd('make install')

    def verify(self):
        """ Verify built program is working.
            Do arbitrary actions to verify.

            return: True only if program works.
        """
        lines = self.cmd('./bin/ag --version', False)
        return lines[0].find('ag version') != -1
```
