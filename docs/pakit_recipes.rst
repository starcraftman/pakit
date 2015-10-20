.. The manual page for writing pakit recipes.

Pakit Recipe Essentials
=======================

Conventions
-----------

- When I write words inside \`backticks\`, the contents should be executed on the shell.
- When I write *recipe*, I am referring to recipes in general as a concept.
- When I write *Recipe*, I am referring to the base class for all recipes at `pakit.Recipe`.
- When I write *Sub.repos*, Sub is just a placeholder for the subclass name you would
  use when writing your Pakit recipe.
  In this case, I am referring to the repos attribute of said subclass.
  More on this later.

Overview
--------
This page will document how to write recipes.

I have tried to make it easy while maintaining the ability for powerful customization.
In order to write recipes...

#. You should be able to program python at a basic level. Writing a class with methods
   should be easy for you. If you want a primer, I recommend: `Dive Into Python`
   (http://www.diveintopython3.net/)
#. You should understand how Pakit works, read the man page and try the demo.
#. You should read the following important pydoc sections:

   a. \`pydoc pakit.Git\` (Fetches git source code)
   b. \`pydoc pakit.Archive\` (Fetches a source archive and extracts)
   c. \`pydoc pakit.Recipe.cmd\` (Wrapper, returns a Command object)
   d. \`pydoc pakit.shell.Command\` (Used to execute system commands)
#. You must know how the program you are writing the recipe for compiles and installs.
#. Later, you can read example recipes in the **pakit_recipes** module.

Annotated Example
-----------------
To quickly explain recipes, I will discuss the **example** recipe
that comes with Pakit.
It doesn't build anything, it just demonstrates all major features including optional ones.
By executing the following commands you can see it in action, pay attention to the output

.. code-block:: bash

  pakit --display example
  pakit --install example
  pakit --remove example exampledep

My annotations will begin with "#" signs like inline python comments.
I will also use method docstrings to explain details.

.. code-block:: python

  # This docstring is not used by pakit, by convention they are usually similar
  """ Formula for building example """

  # All Recipes must be usable on python 2.7+, use future print if needed
  from __future__ import print_function

  # Pakit provides convenience classes, full list available with `pydoc pakit`
  # Import only those you need.
  from pakit import Git, Recipe

  # Feel free to use standard libs provided with python 2.7
  # avoid python 3 specific dependencies
  import os


  # This recipe should be in file 'example.py'
  # It can be referenced by pakit commands as 'example'
  class Example(Recipe):
      """
      Example recipe. This line should be a short description.

      This is a longer description.
      It can be of any length.

      Have breaks in text.
      It will be presented as 'More Information' when displaying a Recipe.
      For instance `pakit --display example`.
      """
      def __init__(self):
          super(Example, self).__init__()
          # Extra attributes are ignored by pakit
          self.src = 'https://github.com/ggreer/the_silver_searcher.git'
          # The homepage of the project, should be information for users
          self.homepage = self.src
          # A dictionary of Fetchable objects, used to get the source code
          # By convention, should always have 'stable' and 'unstable' keys
          # 'stable' -> point to stable release of source code
          # 'unstable' -> point to a more recent version, like a branch of git
          self.repos = {
              'stable': Git(self.src, tag='0.30.0'),
              'unstable': Git(self.src),
          }
          # OPTIONAL: If present, this Recipe requires listed Recipes to be
          #           installed before it can be
          self.requires = ['exampledep']

      def log(self, msg):  # pylint: disable=R0201
          """
          Stupid method, just for tracing flow.

          You can add any method you want to your Recipe subclass.
          """
          print(msg, 'the working directory is', os.getcwd())

      def pre_build(self):
          """
          OPTIONAL: Will be called BEFORE build().

          When called, the working directory will be set to the source code.

          Possible Use Case: Patching source before build().
          """
          self.log('Before build()')

      def build(self):
          """
          MANDATORY

          When called, the working directory will be set to the source code.
          Steps should be taken to build and install the program.
          Issue system commands using self.cmd.
          For usage, see 'pydoc pakit.recipe.cmd` for details.
          """
          self.log('build()')
          cmd1 = self.cmd('pwd')
          cmd2 = self.cmd('ls')
          print('Current dir: ' + cmd1.output()[0])
          print('Contains:\n  ' + '\n  '.join(cmd2.output()))

      def post_build(self):
          """
          OPTIONAL: Will be called AFTER build().

          When called, the working directory will be set to the source code.

          Possible Use Case: Patching files after installed.
          """
          self.log('After build()')

      def pre_verify(self):
          """
          OPTIONAL: Will be called BEFORE verify().

          When called, the working directory will be set to a temporary
          directory created by pakit.
          Your program binaries will be available  at the front of $PATH.
          You may do anything in the temp directory so long as permission
          to delete the files/folder are not removed.

          Possible Use Case: Fetch some remote file to test against.
          """
          self.log('Before verify()')

      def verify(self):
          """
          MANDATORY

          When called, the working directory will be set to a temporary
          directory created by pakit.
          Your program binaries will be available  at the front of $PATH.
          You may do anything in the temp directory so long as permission
          to delete the files/folder are not removed.

          You should execute Commands with self.cmd and verify the output.
          Use 'assert' statements to ensure the build is good.
          """
          self.log('verify()')
          assert True

      def post_verify(self):
          """
          OPTIONAL: Will be called AFTER verify().

          When called, the working directory will be set to a temporary
          directory created by pakit.
          Your program binaries will be available  at the front of $PATH.
          You may do anything in the temp directory so long as permission
          to delete the files/folder are not removed.

          Possible Use Case: Not yet found.
          """
          self.log('After verify()')

Recipe Overview
---------------
The following sections attempt to give a more in depth rundown of each
part of a recipe.

**Recipe Naming**
  explains how to name your recipes and subclasses.

**Recipe Loading**
  explains where to put the recipe for indexing.

**Recipe Fetching**
  details how to specify source code to be retrieved.

**Recipe Building**
  explains how to specify build instructions.

**Recipe Verification**
  details how to verify the recipe succeeded.

Recipe Naming
-------------
In general, the name you pick for the Recipe file is the one you will use throughout
Pakit to interact with the recipe.

In short:

#. Every recipe is defined in its own file.
#. The name of the recipe file, is the name Pakit will use to index it in the database.
#. Each recipe file must contain at least 1 class that is the capitalized name of the recipe file.
#. That class must inherit from `pakit.Recipe`.

For example, the default recipe **ag** found in `pakit_recipes/ag.py`.

#. The recipe is stored in: `pakit_recipes/ag.py`
#. The class is: **class Ag(Recipe): ...**
#. It can be installed by: **pakit -i ag**

Recipe Loading
--------------
All Recipes are indexed by `pakit.recipe.RecipeDB` on startup.
The database uses a dictionary approach to storage, last Recipe loaded with the same name wins.
So if both *default* and *user* paths have a Recipe for **ag**, Pakit will
use the *user* version as it was loaded later.

Now just to clarify:

#. *Default* Recipes will be maintained, tested and provided by Pakit. This project will
   try to ensure these work. Default recipes currently come with pakit in the **pakit_recipes** module.

#. *User* Recipes are ones you write and store in the configured location  `pakit.paths.recipes`
   on your computer. By default, this location is `$HOME/.pakit/recipes`. You are responsible for your
   own Recipes, if you want help writing them try the gitter channel on the project page.

Recipe Fetching
---------------
All Recipes must have an attribute called *repos* that is a dictionary of
Fetchable subclasses.
These subclasses provide convenient means to fetch source code from remote URIs,

Noteworthy Subclasses:

- *Git*: Fetch source from a valid git repository.
  By default checkout default branch.
  Optionally specify a branch, tag, or revision to checkout post download.
- *Hg*: The same as Git but for Mercurial repositories.
- *Archive*: Provides support for retrieving source archives from a specified URI.
  You must provide the hash of the archive to verify it after download.
  Extracting the archive to source folder will be done automatically if supported.
- *Dummy*: A convenience class, should the Recipe not require source code.
  This class will simply create an empty folder where the source should be.

By convention, repos should have two entries: *stable* and *unstable*.
The *stable* repo should fetch a tagged or version release of code if possible.
The *unstable* repo can point to a more recent version directly from source.

The repo selected for a Recipe can be configured, see the **pakit** man page for details.

Recipe Building
---------------
Once the source code selected is downloaded Pakit will automatically change directory to the
source code. It will then invoke the *Sub.build()*.
By the end of the *Sub.build()*, your program should be installed to the required path.
The path to install your program is available in the *Sub.opts* variable, using the *prefix* key.
Linking will be done automatically by Pakit after **build()** and
before the **verify()** method.

A few notes:

#. Any Exception raised during *Sub.build()* method will trigger a rollback, halting
   any further tasks and cleaning up the current install. If it was an update,
   the previous working version will be restored.
#. You are free to use anything available in python and its libraries to build your program,
   even Pakit code.
#. To issue system commands I **STRONGLY** encourage you to use the *Sub.cmd* convenience method
   available on all subclasses.
   It acts as a wrapper around  python's subprocess.Popen, enabling useful features:
   This method returns the Command object after it has finished executing.

  a. It will timeout your Command if no stdout/stderr received during a configured interval.
  b. It will expand dictionary markers against **self.opts**, a dictionary of values configurable
     by the user and Recipe writer. This dictionary includes the source, install and link location for
     the program.
  c. Output can be retrieved with *Command.output()* and returns a list of strings.
  d. If you pass in a prev_cmd to the constructor, you Command will use it for stdin.

For more information about executing system commands see:

- Details about the cmd wrapper at \`pydoc pakit.recipe.Recipe.cmd\`
- Details about the Command class at \`pydoc pakit.shell.Command\`


Recipe Verification
-------------------
Verification exists to ensure the installed program works AFTER having been linked into the link directory.
You working directory will be changed to a temporary directory within which you can do anything
to verify the program. This includes, writing files, invoking commands, building programs against
libraries.

To verify the program, you should use python **assert** statements.
If an AssertionException is raised Pakit will clean up by:

- Undoing the link step.
- Deleting the install folder.
- Reseting or deleting the source code.

.. Text replacements and links go here
