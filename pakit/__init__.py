"""
pakit: Build and manage programs simply.

- A Package Manager CLI to install, remove & update programs.
- A simple Recipe specification to build programs from source code.
- Premade recipes for common programs under ``pakit_recipes``.

See...
- *pakit.conf* for information on configuration, including defaults.
- *pakit.exc* for all exception classes.
- *pakit.main* for all argument parsing and task running logic.
- *pakit.recipe* for information on writing and extending Recipes.
- *pakit.shell* for all code related to shell commands.
- *pakit.task* for all high level tasks like installing and updating.

Configuration is done by YAML file in your $HOME folder.
The default is `~/.pakit.yml`.
"""
from __future__ import absolute_import

from pakit.recipe import Recipe
from pakit.shell import Archive, Git, Hg

__all__ = ['Archive', 'Git', 'Hg', 'Recipe']

__version__ = '0.2.3'
