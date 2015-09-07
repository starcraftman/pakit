# Demo

* This demo should only take about 5 minutes.
* Nothing done in this demo will harm your system.
* `pakit` will put all files under `/tmp/pakit`.
* You should be able to simply copy & paste into a terminal the commands put
inside code boxes. These commands are based on my Ubuntu machine.

## Install

Currently, pakit can't handle dependencies so anything you build has to have
dependencies met by the system. 

**Install Dependencies**

Set up the user build environment to build `ag` & `tmux`. Pakit only really depends
on the commands a recipe needs to execute. On Ubuntu you would need:

```bash
sudo apt-get install build-essential automake git python-pip liblzma-dev libevent-dev ncurses-dev
```

**Get Pakit From Github & Put On $PATH**

We get the source code from git and put it on the path.
Since we aren't installing from pip, we must manually install those packages.

```bash
git clone https://github.com/starcraftman/pakit.git
export PATH=$(pwd)/pakit/bin:$PATH
sudo pip install argparse PyYAML
```

Note: If you installed from pip, above step is not needed.                                                        

**Put Install Location On $PATH**

Pakit will install everthing under `/tmp` by default, so don't worry about conflicts.
All binaries will be under `/tmp/pakit/link/bin` by default, so we will put it on $PATH.

```bash
export PATH=/tmp/pakit/links/bin:$PATH
```

**IMPORTANT**: If you like pakit, you will have to make the above exports permanent.
Do this by adding them to your shell configuration, usually `.bashrc` or `.bash_aliases`.

## Run Commands

Run these commands in order to demonstrate pakit.

**Print Help**

```bash
pakit -h
```

**Write User Config**

Writes the default config to a file in home, default: `~/.pakit.yaml`

```bash
pakit --create-conf
```

**Install Packages**

Install two packages, the grep program `ag` and the screen replacement
`tmux` to `paths.prefix` and link to `paths.link`. May take a while.

```bash
pakit -i ag tmux
```

**Check Programs**

Verify that installed programs work.

* `which` should print out location of binary.
* `ag` command will search your hidden shell files for `export` commands.                                         

```bash
which ag
ag --hidden --depth 2 --shell export
```

**Remove Package**

Simple remove, no trace will be left.

```bash
pakit -r tmux
```

**List Available Recipes**

Prints out any recipe pakit can run.

```bash
pakit -a
```

**List Installed Programs**

Prints out recipes that have installed programs.

```bash
pakit -l
```
                                                                                                                  
**Edit Config**

Now to demonstrate configuration, let us change `ag` from building from the
last `stable` release to the latest commit (i.e. `unstable`).

Edit your `~/.pakit.yaml` file and add the following line at the end. Save and exit.

```yaml
ag:
  repo: unstable
  
All recipes should have a `stable` and `unstable` source at least.
This newly added `ag` section, overrides the `defaults` section only for the `ag` recipe.

**Update Packages**:

Updates all recipes on the system. If there are new commits on the branch, a tag has
been changed or the URI/archive has changed it should force a rebuild of the new source.
At this time, `ag` will be rebuilt from the latest commit to its repostiory.

```bash
pakit -u
```

**Verify Update Changed Ag**

This command should list a different hash than before. You may have to scroll up to confirm.

```bash
pakit -l
```
