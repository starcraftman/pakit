# PakIt

[![Travis](https://travis-ci.org/starcraftman/pakit.svg?branch=master)](https://travis-ci.org/starcraftman/pakit)
[![Coveralls](https://coveralls.io/repos/starcraftman/pakit/badge.svg?branch=master&service=github)](https://coveralls.io/github/starcraftman/pakit?branch=master)
[![Stories in Ready](https://badge.waffle.io/starcraftman/pakit.svg?label=ready&title=Ready)](http://waffle.io/starcraftman/pakit)
[![Join the chat at https://gitter.im/starcraftman/pakit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/pakit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Python](https://img.shields.io/pypi/pyversions/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![License](https://img.shields.io/pypi/l/Django.svg)](https://pypi.python.org/pypi/pakit)
[![Version](https://img.shields.io/pypi/v/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![Status](https://img.shields.io/pypi/status/pakit.svg)](https://pypi.python.org/pypi/pakit)

## Description

It is a small, python based package manage that builds from source.

Want a longer explanation? Skip to the [Overview](https://github.com/starcraftman/pakit#overview) section.

## Try Pakit In 5 Minutes

### Install

Currently, pakit can't handle dependencies so anything you build has to have
dependencies met already. Work in progress.

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

### Run Commands

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
```

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

## More Information

From inside the pakit source folder:

* Consult man: `man pakit`

* Read pydocs: `pydoc pakit` or `pydoc pakit.shell` and so on...

* Read `DESIGN.md` for details on design. A bit out of date.

* See [Waffle](http://waffle.io/starcraftman/pakit) for things I'm working on.

## Dev Setup

Install all development packages: `python setup.py deps`

To run the test suite: `tox`

## Overview

Basically I want to make a universal package manager on python.
Runs everywhere, builds anything and handles dependencies.
A bit like a meta build tool tying arbitrary recipes together.
At the end of the day, will probably resemble Homebrew at least a little.

Importantly, the recipes should be configurable via a single YAML file
that users can modify without changing the recipes. Say you want to pass
particular flags to the `vim` or `ag` build, you'd just put them in an entry
in the config.

To be clear this is NOT a replacement for system package managers like apt, yast and so on.
It is intended primarily to be a supplementary package manage like homebrew or pip.
You install bleeding edge packages with it and then put onto your PATH the paths.link location.
Later on, if I can, I may try to add bootstrapping logic for primitive/embedded areas
or just to isolate against bad dev environments.

Expected Feature Overview:
* Python only, with minimal dependencies.
* Package manager interface, install remove and update recipes.
* 100% tested, framework & supported recipes.
* Should work on any POSIX system, emphasis on Linux.
* Simple recipe specification.
* Configuration via a single YAML file.
* Available via [`pip`](https://pypi.python.org/pypi/pakit).
* Traceability via logs for every command.
* Premade & tested recipes available for use.

See [DESIGN.md](https://github.com/starcraftman/pakit/blob/master/DESIGN.md) for more details.

## Roadmap
For accurate plan, see waffle.io link above.
Just a rough guess of what I should be implementing when.

### 0.1
- [x] Implement basic tasks to install & remove 'ag' program.
- [x] Support Git & Hg repositories.
- [x] Simple config from `.pakit.yaml`.
- [x] Upgrade logic.
- [x] User defined recipe locations via config.
- [x] Pick a license.
- [x] Pip/Wheel upload.

### 0.2
- [x] Add archive support, supports download, hashing & extracting.
  - [x] Tar (tarfile)
  - [x] Zip (zipfile)
  - [x] tar.xz (xz command)
  - [x] Rar (rar command)
  - [x] 7z (7z command)
- [x] Add list & searching support.
- [x] Python 3 support
- [x] Better error handling, rollback
- [ ] Improve Command, timeout & input file
- [ ] Investigate alternatives/improvements to RecipeDB

### 0.3
- [ ] Dependency logic between recipes tasks.

### 0.4
- [ ] Parallelism, envisioned as some task based dependency.

### Beyond
- [x] Make an organization. [pakit](https://github.com/pakit)
- [ ] Formulas go to separate repo.
- [ ] Create tool to convert homebrew ruby formula. Maybe?
- [ ] Make a simple io website & promote?
