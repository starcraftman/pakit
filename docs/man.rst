.. The manual page for pakit.

Man Page
========

Description
-----------
PakIt provides:

#. A Package Manager CLI to install, remove & update programs.
#. A simple Recipe specification to build programs from source code.
#. Premade recipes for common programs under ``pakit_recipes``.

Synopsis
--------
**pakit** [options] [RECIPE...]

Options
-------
-a, --available
   List available recipes

--available-short
   List available recipes, output is very terse

-c,  --conf CONF
   Use CONF file instead of default (~/.pakit.yaml)

--create-conf
   Write the default configuration to CONF

-d, --display RECIPE [RECIPE...]
   Show detailed information on RECIPE(s)

-h, --help
   Show a short help message

-i, --install RECIPE [RECIPE...]
   Installs the RECIPE(s) to the system

-k, --search WORD [WORD...]
   Search names & descriptions for WORD(s)

-l, --list
   List installed recipes

--list-short
   List installed recipes, output is very terse

-r, --remove RECIPE [RECIPE...]
   Removes the RECIPE(s) on the system

-u, --update
   Updates all recipes on the system

-v, --version
   Show the program version number

Completion
----------
I have written a bash completion script. You can find it within the pakit module, inside the
`extra/completion` folder. See that folder's `README.md` for further details.

Config
------
Configuration is done by YAML file, default location is ``/.pakit.yaml``

This is an example config:

.. code-block:: yaml

   defaults:
      repo: stable
   log:
      enabled: true
      file: /tmp/pakit/main.log
   paths:
      link: /tmp/pakit/links
      prefix: /tmp/pakit/builds
      recipes: /home/username/.pakit/recipes
      source: /tmp/pakit/src
   ag:
      repo: unstable

Expalnation of Config:

log.enabled
   Toggles the file logger. Console errors always enabled.

log.file
   Where the log file will be written to.

paths.link
   Path that should be appended to your shell $PATH.

paths.prefix
   All recipes will be installed into this path.
   Using the above config, the recipe **ag** would be installed to
   **/tmp/pakit/builds/ag**.

paths.recipes
   Path to a folder with user created recipes. Path must be a valid package
   name according to python rules. Importantly this means base folder
   can **NOT** be a hidden directory (leading '.').

paths.source
   The path where source code will be downloaded & built.

defaults
   A dictionary of default options made available to all recipes.
   Anything in this, will be available inside recipes as **self.opts**.

defaults.repo
   The default source repository to use.
   By convention, **stable** will always fetch a stable versioned release.
   Whereas **unstable** is essentially building off the **master** branch of a project.

ag
   A recipe specific dictionary that will *override* keys of the same
   name in **defaults**.

ag.repo
   By setting this to **unstable**, you are instructing pakit to override the
   **defaults** setting and always get the latest version of ag from **unstable**.

Recipes
-------
Recipes are defined in the **pakit_recipes** package inside pakit (for now).

* Every recipe is defined in its own file.
* The name of the recipe file, is the name pakit will use to invoke the recipe.
* Each recipe file must contain at least 1 class that is the capitalized name of the recipe.
* That class must inherit from **pakit.Recipe**.

For example, for recipe **ag**.

* The recipe is stored in: **pakit_recipes/ag.py**
* The class is: **class Ag(Recipe): ...**
* It can be installed by: **pakit -i ag**

For recipe writing details, see ``pydoc pakit.recipe`` and the examples in **pakit_recipes**.
