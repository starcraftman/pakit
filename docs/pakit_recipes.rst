.. The manual page for pakit.

Pakit Recipe Essentials
=======================

Description
-----------
This page should provide all information needed to write a Recipe for pakit.
Before reading this, be sure you understand how pakit works by reading the **pakit** man page.

I will try not to be too specific about code, for more information on classes mentioned
and internal code see the pydocs.

Note on convetion used here, when I write *Recipe.repos*, Recipe here is just a placeholder
for the subclass of Recipe you define. In this case, repos is an attribute. Whereas, *Recipe.build()*
would refer to a method in said subclass of Recipe.

Quick Annotated Example
-----------------------
To facilitate getting quickly up to speed, I will annotate the default **ag** Recipe
to explain how it fits into pakit. Optional attributes or methods will

.. code-block:: python

   """ formula for building example, stored in example.py """
   from pakit import Git, Recipe

  class Ag(Recipe):
      """
      Short description of the program, only 1 line.

      Longer description of the program.
      Can be many lines.

      Formatted any way you like. It will be made available
      as additional information at the bottom of a Recipe
      when displayed with `pakit --display`.
      """
      def __init__(self):
          super(Ag, self).__init__()
          self.src = 'https://github.com/ggreer/the_silver_searcher.git'
          self.homepage = self.src
          self.repos = {
              'stable': Git(self.src, tag='0.31.0'),
              'unstable': Git(self.src),
          }

      def build(self):
          self.cmd('./build.sh --prefix {prefix}')
          self.cmd('make install')

      def verify(self):
          lines = self.cmd('ag --version').output()
          assert lines[0].find('ag version') != -1


For more recipe writing details, see ``pydoc pakit.recipe`` and the examples in **pakit_recipes**.

Recipe Basics
-------------
I have attempted to make pakit Recipes small and light. Most of the work is done behind the scenes
within the base Recipe. All you need to do is follow the conventions below and pakit will do the rest.

By convention, you must follow correct **naming** for your recipes to be **loaded** properly
by pakit. Please see the respective sections for information. After that, you must write a recipe
that describes...

1. How to **fetch** the source code.
2. Steps to **build** and install the source code into a silo.
3. A means to **verify** the build was sucessful.

Recipe Naming
-------------
In general, the name you pick for the Recipe file is the one you will use throughout
pakit to interact with the recipe.

In short:

1. Every recipe is defined in its own file.
2. The name of the recipe file, is the name pakit will use to import, load and store it in the database.
3. Each recipe file must contain at least 1 class that is the capitalized name of the recipe file.
4. That class must inherit from **pakit.Recipe**.

For example, the default recipe **ag** found in **pakit_recipes/ag.py**.

1. The recipe is stored in: **pakit_recipes/ag.py**
2. The class is: **class Ag(Recipe): ...**
3. It can be installed by: **pakit -i ag**

Recipe Loading
--------------
All Recipes are written from the same building blocks, they differ only in who maintains them.

1. *Default* Recipes will be maintained, tested and provided by **pakit**. This project will
   try to ensure these work. Default recipes currently come with pakit in the **pakit_recipes** module.

2. *User* Recipes are ones you write and store in the configured location  `pakit.paths.recipes`
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

- *Git*: Fetch source from a valid git URI. By default checkout default branch. Optionally specify
  a branch, tag, or revision to checkout post download.
- *Hg*: Operates same as Git but for Mercurial repositories.
- *Archive*: Provides support for retrieving source archives from a specified URI. Note you **MUST**
  provide the required hash as argument to verify the integrity of the archive.
- *Dummy*: A convenience class, should the Recipe require a method not yet implemented, use this
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

1. Any Exception raised during **build()** will trigger a rollback of the entire Recipe, halting
   any further tasks and cleaning up the source code.
2. To issue system commands I **STRONGLY** encourage you to use the *Recipe.cmd* convenience method.
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

- *Recipe.pre_build()*
- *Recipe.post_build()*
- *Recipe.pre_verify()*
- *Recipe.post_verify()*

Say for instance, a bug is found in a stable release. You can freely patch the source code during the *pre_build()*
function before actually building it and remove the logic later when a release is made without polluting *build()*.
Alternatively, perhaps you want to patch some file of a build assuming it builds correctly or verifies, see the
relevant post.

Pre and post functions will execute in the same working directory as their main function. That means:

- *pre_build* and *post_build* will have working directory set to the source code.
- *pre_verify* and *post_verify* will have working directory set to the temp directory.

