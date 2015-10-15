.. The manual page for pakit.

Pakit Recipe Essentials
=======================

Description
-----------
This page should provide all information needed to write a Recipe for pakit.
Before reading this, be sure you understand how pakit works by reading the **pakit** man page.

I will try not to be too specific about code, for more information on classes mentioned
and internal working of pakit see the pydocs starting at `pydoc pakit`.

Note on convetion used here, when I write *Recipe.repos*, Recipe is just a placeholder
for the subclass of Recipe you define.
In this case, I am referring to the repos attribute of the subclass Recipe.

Annotated Example
-----------------
To quickly explain Recipes, I will annotate and discuss the **example** Recipe
that comes with pakit.
It doesn't build anything useful, it just demonstrates Recipe features
By executing the following commands you can see it in action, pay attention to
the stdout from pakit.

.. code-block:: bash

  pakit --display example
  pakit --install example
  pakit --remove example exampledep

My annotations will begin with `#` like inline python comments.
I may also make use of the docstrings.
Some of the features of this example are optional, I will make note of this.
Later you can compare what you've seen here with other Recipes that actually
build programs.

.. code-block:: python

  # This docstring is not used by pakit, by convention they are usually similar
  """ Formula for building example """

  # All Recipes must be usable on python 2.7+, use future print if needed
  from __future__ import print_function

  # Pakit provides convenience classes, full list available with `pydoc pakit`
  # Import only those you need.
  from pakit import Git, Recipe

  # Feel free to use standard libs provided with python 2.7
  # Pay attention to avoid python 3 specific ehancements/libs
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
          # Required
          super(Example, self).__init__()
          # Extra attributes are ignored by pakit
          self.src = 'https://github.com/ggreer/the_silver_searcher.git'
          # The homepage of the project, should be information for users
          self.homepage = self.src
          # A dictionary of Fetchable classes, used to get the source code
          # By convention, should always have 'stable' and 'unstable' keys
          # 'stable' -> point to stable release of source code
          # 'unstable' -> point to a more recent version, like branch of code
          self.repos = {
              'stable': Git(self.src, tag='0.30.0'),
              'unstable': Git(self.src),
          }
          # OPTIONAL: If present, this Recipe requires listed Recipes to be
          #           installed before it can be.
          self.requires = ['exampledep']

      def log(self, msg):  # pylint: disable=R0201
          """
          Simple method prints message followed by current working directory.

          You can add any method you want to Recipe so long as pakit's
          conventions are followed. I currently do no checking  to ensure
          they are.
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

For more Recipe writing details, continue reading the following sections.
For additional information on how Recipes work:

* Consult `pydoc pakit.recipe`.
* Read some Recipe examples inside the **pakit_recipes** module.

Recipe Basics
-------------
I have attempted to make pakit Recipes small and light. Most of the work is done behind the scenes
within the base Recipe. All you need to do is follow the conventions and pakit will do the rest.

You must follow correct :ref:`my-recipe-naming` Recipe Naming for your recipes to be **loaded** properly by pakit.
Please see the respective sections for information.
After that, you must write a recipe that describes...

#. How to **fetch** the source code.
#. Steps to **build** and install the source code into a silo.
#. A means to **verify** the build was sucessful.

.. _my-recipe-naming:

Recipe Naming
-------------
In general, the name you pick for the Recipe file is the one you will use throughout
pakit to interact with the recipe.

In short:

#. Every recipe is defined in its own file.
#. The name of the recipe file, is the name pakit will use to import, load and store it in the database.
#. Each recipe file must contain at least 1 class that is the capitalized name of the recipe file.
#. That class must inherit from **pakit.Recipe**.

For example, the default recipe **ag** found in **pakit_recipes/ag.py**.

#. The recipe is stored in: **pakit_recipes/ag.py**
#. The class is: **class Ag(Recipe): ...**
#. It can be installed by: **pakit -i ag**

Recipe Loading
--------------
All Recipes are written from the same building blocks, they differ only in who maintains them.

#. *Default* Recipes will be maintained, tested and provided by **pakit**. This project will
   try to ensure these work. Default recipes currently come with pakit in the **pakit_recipes** module.

#. *User* Recipes are ones you write and store in the configured location  `pakit.paths.recipes`
   on your computer. By default, this location is `$HOME/.pakit/recipes`. You are responsible for your
   own Recipes, if you would like help try the gitter channel on the project page.

All Recipes are indexed by RecipeDB, which uses a dictionary approach to storage. Last Recipe loaded
with the same name wins. So if both *default* and *user* paths have a Recipe for **ag**, pakit will
use the *user* version as it was loaded later.

Recipe Fetching
---------------
All Recipes **MUST** have an attribute called *Recipe.repos* that is a dictionary of
Fetchable subclasses.
These subclasses provide convenient means to fetch source code from remote URIs,

Example Subclasses:

* *Git*: Fetch source from a valid git URI. By default checkout default branch. Optionally specify
  a branch, tag, or revision to checkout post download.
* *Hg*: Operates same as Git but for Mercurial repositories.
* *Archive*: Provides support for retrieving source archives from a specified URI. Note you **MUST**
  provide the required hash as argument to verify the integrity of the archive.
* *Dummy*: A convenience class, should the Recipe require a method not yet implemented, use this
  and no source will be downloaded. You will have to do it yourself in other parts of the Recipe
  like **build**.

By convention, repos should have two entries by default: *stable* and *unstable*.
At the very least, provide *stable* as it will usually be the default user setting.
As the names imply, *stable* should point to a tag or official release of the project.
*unstable* can point to the source repository or some more recent edition.

The repo selected from repos can be configured, see the **pakit** man page for details.

Recipe Building
---------------
Once the source code selected is downloaded **pakit** will automatically change directory to the
source code. It will then invoke the *Recipe.build()* function to do work. Within this function
you may use whatever python function is available with python 2.7 by default, or any of pakit's
internal Classes.

A few notes:

#. Any Exception raised during **build()** will trigger a rollback of the entire Recipe, halting
   any further tasks and cleaning up the source code.
#. To issue system commands I **STRONGLY** encourage you to use the *Recipe.cmd* convenience method.
   It acts as a wrapper around  subprocess.Popen, enabling some useful features:

  A. It will timeout your Command if no stdout/stderr received during a configured interval.
  B. It will expand dictionary markers against **self.opts**, a dictionary of values configurable
     by the user and Recipe writer. This dictionary includes the source, install and link location for
     the program.

For more information on the Command class see the pydoc for **pakit.shell.Command**.

By the end of the **build()** function, your program should be installed to the required path.
The path to install your program is available in the *Recipe.opts* variable, using the *prefix* key.

Recipe Verification
-------------------
Once again, execute any arbitary combination of python code and system commands with self.cmd
to verify the proper functioning of the Recipe. You should make liberal use of the **assert**
keyword. Any raised AssertionException will trigger a rollback like above, undoing linking
and cleaning up modifications.

Of important note, unlike *Recipe.build()* your working directory will be a temporary directory
created by python's tempfile. You may do **anything** you need to verify the program within,
like writing a C file and checking it compiles against a built library, or writing a file and
checking **ag** can grep it correctly. On function exit, the temp directory will be completely cleaned.

Recipe Pre And Post Functions
-----------------------------
To faciliatate some corner cases, I've provided the ability to separate some logic into pre and post functions
for both *Recipe.build()* and *Recipe.verify()*. To be clear that means implementing these in your class would be:

* *Recipe.pre_build()*
* *Recipe.post_build()*
* *Recipe.pre_verify()*
* *Recipe.post_verify()*

Say for instance, a bug is found in a stable release. You can freely patch the source code during the *pre_build()*
function before actually building it and remove the logic later when a release is made without polluting *build()*.
Alternatively, perhaps you want to patch some file of a build assuming it builds correctly or verifies, see the
relevant post.

Pre and post functions will execute in the same working directory as their main function. That means:

* *pre_build* and *post_build* will have working directory set to the source code.
* *pre_verify* and *post_verify* will have working directory set to the temp directory.
