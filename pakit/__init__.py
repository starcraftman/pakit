"""
PakIt: Build and manage programs simply

In short, Recipes are defined and put in the pakit_recipes directory. These
recipes subclass Recipe, providing information on how to build a program.
Pakit will dynamically import and instantiate the recipes at run time.
For more information see pakit.recipe

Configuration is done by a YAML file in your HOME folder.
The default is `~/.pakit.yaml`.
Here you can tell pakit where to install and link programs.
You can also set default and recipe specific options.
For more information see pakit.conf

All possible actions are defined under pakit.task.
"""
from __future__ import absolute_import

from pakit.recipe import Recipe
from pakit.shell import Archive, Git, Hg

__all__ = ['Archive', 'Git', 'Hg', 'Recipe']

__version__ = '0.2.2'
