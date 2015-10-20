# Demo

- This demo should take about 5 minutes.
- Nothing done in this demo will harm your system.
- Pakit will put all files under `/tmp/pakit`.
- You should be able to simply copy & paste the following commands into a terminal.
  These commands are based on my Ubuntu machine.

## Before Starting

Please see the installation steps & notes in `README.md`.
You may also find it useful to consule the man page if anything requires clarification.

## Run Commands

Run these commands in order to demonstrate Pakit.

**Write User Config**

Writes the default configuration to a file in home, default: `$HOME/.pakit.yml`
This configuration can be edited by a user to alter Pakit's behaviour.

```bash
pakit --create-conf
```

**Install Packages**

Install two packages, the fast grep like program `ag` and the screen replacement
`tmux` to `pakit.paths.prefix` and link to `pakit.paths.link`. May take a while.

```bash
pakit --install ag tmux
```

**Check Programs**

Verify that installed programs work.

1. The `which` command should print out location of binary.
2. The `ag` command will search your hidden shell files for `export` commands.

```bash
which ag
ag --hidden --depth 2 --shell export
```

**Remove Package**

Simple remove, no trace will be left. Only removes tmux.

```bash
pakit --remove tmux
```

**More Information On Recipe**

Prints out information including description, requirements, repositories to fetch
source code and any additional notes.

```bash
pakit --display ag vim
```

**List Available Recipes**

Prints out any recipe Pakit can install.

```bash
pakit --available
```

**List Installed Programs**

Prints out recipes that have been installed onto the system.

```bash
pakit --list
```

**Edit Config**

Now to demonstrate configuration options.
Let us change the repository `ag` builds from `stable` to `unstable`.
This will force an update since we have specified a different revision to build from.

Edit your `$HOME/.pakit.yml` file and add the following line at the end. Save and exit.

```yaml
ag:
  repo: unstable
```

This newly added `ag` section, overrides the `defaults` section only for the `ag` recipe.

**Update Packages**:

Updates all recipes on the system.
If there are new commits on the branch, a tag has been changed or
the URI/archive has changed it should force a rebuild of the new source.
At this time, `ag` will be rebuilt from the latest commit to its repository.

```bash
pakit --update
```

**Verify Update Changed Ag**

This command should list a different hash than before. You may have to scroll up to confirm.

```bash
pakit --list
```

## More Information

- pakit --help
- man pakit
- pydoc pakit
