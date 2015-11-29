"""
pakit: A python based package manager that builds programs from source

1. A Package Manager CLI to install, remove & update programs.
2. A simple Recipe specification to build programs from source code.
3. Premade recipes for common programs available maintained by pakit at
   https://github.com/pakit/base_recipes) maintained by pakit.

When you install a program Pakit will...

1. download the source into a silo in `pakit.paths.source` and build it.
2. install the program into a silo under `pakit.paths.prefix`.
3. link the silo to the `pakit.paths.link` directory.

See...
- *pakit.conf* for information on configuration, including defaults.
- *pakit.exc* for all exception classes.
- *pakit.graph* for all graphing code.
- *pakit.main* for all argument parsing and task running logic.
- *pakit.recipe* for information on writing and extending Recipes.
- *pakit.shell* for all code related to shell commands.
- *pakit.task* for all high level tasks like installing and updating.

Configuration is done by YAML file in your $HOME folder.
The default is `$HOME/.pakit.yml`.
"""
from __future__ import absolute_import

from pakit.recipe import Recipe
from pakit.shell import Archive, Dummy, Git, Hg

__all__ = ['Archive', 'Dummy', 'Git', 'Hg', 'Recipe']

__version__ = '0.2.5'
