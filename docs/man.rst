.. The manual page for pakit.

Pakit
=====

Description
-----------
pakit provides:

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
   Use CONF file instead of default (~/.pakit.yml)

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

--relink
   Relink installed recipes

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
Configuration is done by YAML file, default location is ``~/.pakit.yml``

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
       recipes: /home/starcraftman/.pakit/recipes
       source: /tmp/pakit/src
   ag:
     repo: unstable

Expalnation of Config:

pakit.command.timeout
   The timeout for commands, when no stdout produced for timeout kill process.

pakit.log.enabled
   Toggles the file logger. Console are errors always enabled.

pakit.log.file
   Where the file log will be written to.

pakit.log.level
   The level to write to the file log.

pakit.paths.link
   Path where all programs will be linked to. You should put the bin folder in
   this folder on the **$PATH**. For the above config, **PATH=/tmp/pakit/links/bin:$PATH**.

pakit.paths.prefix
   All recipes will be installed into this path. Using the above config,
   the recipe **ag** would be installed to **/tmp/pakit/builds/ag**.

pakit.paths.recipes
   Path to a folder with user created recipes. Path must be a valid package
   name according to python rules. Importantly this means base folder
   can **NOT** be a hidden directory (leading '.').

pakit.paths.source
   The path where source code will be downloaded & built.

pakit.defaults
   A dictionary of default options made available to all recipes.
   Anything in this, will be available inside recipes as **self.opts**.

pakit.defaults.repo
   The default source repository to use.
   By convention, **stable** will always fetch a stable versioned release.
   Whereas **unstable** should build from recent project commits, it may break.

ag
   A recipe specific dictionary that will *override* keys of the same
   name in `pakit.defaults`.

ag.repo
   Setting **unstable** here overrides the value of `pakit.defaults.repo`.

More Help
---------
To get more information...

