.. The manual page for pakit.

Pakit
=====

Description
-----------
Pakit provides:

#. A package manager interface to install, remove & update programs.
#. A simple Recipe specification to build programs from source code.
#. Premade recipes for common programs under ``pakit_recipes``.

When you install a program Pakit will...

#. download the source into a silo in `pakit.paths.source` and build it.
#. install the program into a silo under `pakit.paths.prefix`.
#. link the silo to the `pakit.paths.link` directory.

Synopsis
--------
**pakit** [options] [RECIPE...]


Subcommands
-----------
See each subcommands `--help` for additional information.

create-conf CONF
  Create the default configuration at CONF.
  If not specified, use default at: ~/.pakit/pakit.yml

install RECIPE [RECIPE...]
  Install selected recipes.

remove RECIPE [RECIPE...]
  Remove selected recipes.

update
  Update all recipes. If args, update only selected recipes.

display RECIPE [RECIPE...]
  Show information about selected recipes.

list
  List all installed recipes.

available
  List all recipes that can be installed.

relink
  Relink all or selected recipes.

search WORD [WORD...]
  Search against recipes for WORDS specified.
  WORD is delimited by space.

Options
-------
-c,  --conf CONF
    Use CONF file instead of default ($HOME/.pakit.yml)

-h, --help
    Show a short help message

-v, --version
    Show the program version number

Completion
----------
At this time only bash completion is available
You can find it within the site package at  `pakit/extra/completion`.
See that folder's `README.md` for further details.

Config
------
Configuration is done by YAML file, default location is ``$HOME/.pakit.yml``

This is an example config:

.. code-block:: yaml

  pakit:
    command:
      timeout 120
    defaults:
      repo: stable
    log:
      enabled: true
      file: /tmp/pakit/main.log
      level: debug
    paths:
      link: /tmp/pakit/links
      prefix: /tmp/pakit/builds
      recipes: /home/starcraftman/.pakit
      source: /tmp/pakit/src
    recipe:
      update_interval: 86400
      uris:
      - uri: https://github.com/pakit/base_recipes
      - uri: user_recipes
      - uri: https://github.com/pakit/example
        branch: dev
      - uri: https://github.com/pakit/example
        tag: 0.2.2
  ag:
    repo: unstable

I will explain each element of the nested dictionary in turn.

pakit.command.timeout
    The timeout for commands.
    When no stdout produced for timeout seconds kill the process.

pakit.log.enabled
    Toggles the file logger. Console errors are always enabled.

pakit.log.file
    Where the file log will be written to.

pakit.log.level
    The level to write to the file log.

pakit.paths.link
    Path where all programs will be linked to.
    You should put the bin folder in this folder on the `$PATH`.
    For the above config, `PATH=/tmp/pakit/links/bin:$PATH`.

pakit.paths.prefix
    All recipes will be installed inside their own silos here.
    Using the above config, the recipe `ag` would be
    installed under `/tmp/pakit/builds/ag`.

pakit.paths.recipes
    Path to a folder where all recipes will be stored.
    All recipes will be specified in the `pakit.recipe.uris` node.

pakit.paths.source
    The path where source code will be downloaded & built.

pakit.recipe.update_interval
    After a recipe uri has not been updated for update_interval seconds
    check for updates.

pakit.recipe.uris
    The list contains a series of dictionaries that specify recipes.
    Recipes are indexed in the order of the list.
    Each dictionary must contain the 'uri' key as described below.
    Any other keys will be passed to pakit.shell.vcs_factory as kwargs.
    Remotely fetched recipes will be periodically updated.

    The 'uri' key must be one of ...

    - A version control uri supported by `pakit.shell.vcs_factory`
      like git or mercurial.
    - A simple folder name to be used in `pakit.paths.recipes`.

pakit.defaults
    A dictionary of default options made available to all recipes.
    Anything in this, will be available inside recipes as self.opts.

pakit.defaults.repo
    The default source repository to use.
    By convention, "stable" should always fetch a stable versioned release.
    Whereas "unstable" should build from recent project commits.

ag
    A recipe specific dictionary that will override keys of the same
    name in `pakit.defaults`.

ag.repo
    Setting "unstable" here overrides the value of "pakit.defaults.repo".

More Help
---------
To get more information...

- pakit --help
- man pakit_recipes
- pydoc pakit
