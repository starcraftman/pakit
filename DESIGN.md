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

* File config by hidden YAML file at `~/.wok.yml`.

* install_to:   Folder that will contain built programs
* link_to:      The folder you will put on your path
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

Work In Progress

Probably going to be a python class.
Should provide helpers to facilitate common tasks like download/extract archive.
User has choice between stable release & source build.

Example:
```py
from wok import Recipe, cmd, git

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
