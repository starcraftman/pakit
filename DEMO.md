# Demo

- This demo should take about 5 minutes
- Nothing done in this demo should harm your system
- Pakit will install all files under `/tmp/pakit`
- Some configs will be written to`~/.pakit.yml` and `~/.pakit/`
- Copy & paste the following commands into a terminal

## Before Starting

Please see the installation steps in the [README.md](https://github.com/starcraftman/pakit/tree/sub_com#install-pakit).
See the end of the demo for extra information.

## Run Commands

**Write User Config**

The default configuration is written to: `~/.pakit.yml`
See the man page for a breakdown of the file.

```bash
pakit create-conf
cat ~/.pakit.yml
```

**Install Programs**

To start we will install two programs, `ag` and `tmux`.

During the command pakit will:
- Download source to `pakit.paths.source`
- Build the source in that dir, then install to `pakit.paths.prefix`
- Link the installed files to `pakit.paths.links`

```bash
pakit install ag tmux
```
**List Installed Programs**

```bash
pakit list
```

**Check Programs**

Now to verify the installations...

1. The `which` command should print the newly built tmux.
1. The `ag` command will print matching lines from the config.

```bash
which tmux
ag tmp ~/.pakit.yml
```

**Remove Program**

Now remove `tmux` and confirm it is gone.

```bash
pakit remove tmux
which tmux
```

**More Information On A Recipe**

Print out information about a recipe, including configured repo and requirements.

```bash
pakit display ag vim
```

**List Available Recipes**

Print out the recipes Pakit can install.
Default recipes are stored inside `~/.pakit/base_recipes`

```bash
pakit available
```

**Edit Config**

To demonstrate configuration options I will change the repo `ag` uses.
By default it downloads and builds a tagged release from the `stable` repo.
Changing it to `unstable` will force it to build from the latest commit on master.

Now edit `~/.pakit.yml` and add the following section to the end. Save and exit.

```yaml
ag:
  repo: unstable
```

**Update Recipes**:

A recipe will be updated when ...
- the configured repo changes.
- the recipe is tracking a branch with a new commit.
- the recipe is tracking a tag and it has changed.
- the recipe is built from an archive and the archive URI has changed.

The repo for `ag` just changed so it will be updated.

```bash
pakit update
```

**Verify Update Changed Ag**

The hash listed is different than the previous one.

```bash
pakit list
```

**Search Recipes**

Simple search support is available.
By default the search is not case sensitive and matches against recipe names or descriptions.

```bash
pakit search vim
```

## Demo Clean Up (Optional)

Removing all files pakit made is simple.

1. Uninstall pakit, depends on how you installed it
  - **git**: `rm -rf pakit`
  - **pip**: `sudo -H pip uninstall pakit`
1. `rm -rf /tmp/pakit ~/.pakit ~/.pakit.yml`

## More Information

More information is available is available from ...

- `pakit --help`
- `man pakit`
- `man pakit_recipes`
- `pydoc pakit`
