## First Command Line

- `pakit install tmux ag`       -- Install several programs
- `pakit update`                -- Update local programs
- `pakit remove tmux`           -- Remove program
- `pakit list`                  -- List installed programs
- `pakit available`             -- List ALL available formula
- `pakit search lib`            -- Display matching avilable recipes
- `pakit --conf a.yaml list`    -- Override default config
- `pakit display vim ag`        -- Display package information
- `pakit relink`                -- Relink all programs

Short opts: No longer supported with subcommand model.

## Configuration

See one of the following for up to date configuration:
- pydoc pakit.conf
- man pakit

## Recipe Specification

Work In Progress

Below is an example, taken from pakit_recipes/ag.py.
Core logic implemented in pakit/recipe.py
Aim is to have very short easily written recipes.

Parts of standard recipe:
- description: Short 1 line description. First non-empty line of __doc__.
- more_info: Long as you want. second non-empty line of __doc__ to end.
- homepage: Where people can get information on the project.
- repos: A dict of possible source downloaders. See pakit.shell.Fetchable and subclasses.
- build(): A function that builds the source selectable by config.
- verify(): A function that uses `assert` statements to verify build.

Example recipe with heavy documentation available with base_recipes.
Please see ~/.pakit/base_recipes/example.py for more details.

## Dependencies:

For first attempt, implement simple dependency on 'stable' repos only.
Recipe A depends on B & C, then InstallTasks would be (B C A) or (C B A).

In Recipes Constructor to depend on Git and Hg:
    self.requires = ['git', 'hg']

To determine order, will have to make a directed graph  based on requirements requested.
Then perform a topological sort to get a list of execution.
While Pakit single threaded can return a list of tasks to be iterated in order.

For multithreaded version, should make some queue like adapter for the DAG so that
can lock and pop off one task at a time when requirements met. Else idle the worker.
