# Pakit

[![Travis](https://travis-ci.org/starcraftman/pakit.svg?branch=master)](https://travis-ci.org/starcraftman/pakit)
[![Coveralls](https://coveralls.io/repos/starcraftman/pakit/badge.svg?branch=master&service=github)](https://coveralls.io/github/starcraftman/pakit?branch=master)
[![Stories in Ready](https://badge.waffle.io/starcraftman/pakit.svg?label=ready&title=Ready)](http://waffle.io/starcraftman/pakit)
[![Join the chat at https://gitter.im/starcraftman/pakit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/pakit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Python](https://img.shields.io/pypi/pyversions/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![License](https://img.shields.io/pypi/l/Django.svg)](https://pypi.python.org/pypi/pakit)
[![Version](https://img.shields.io/pypi/v/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![Status](https://img.shields.io/pypi/status/pakit.svg)](https://pypi.python.org/pypi/pakit)

## Description

It is a small, python based package manager that builds from source.

![Pakit Demo](https://github.com/pakit/demo/raw/master/demo.gif)

Want a longer explanation? Skip to the [Overview](https://github.com/starcraftman/pakit#overview) section.

**[Try the demo yourself after installing!](https://github.com/starcraftman/pakit/blob/master/DEMO.md#demo)**

## Install Pakit

To use pakit:

1. Ensure you have a **build environment** for compiling the programs.
2. Fetch pakit via **pip** or **github**.
3. Modify your **$PATH**.

**Build Environment**

For now, pakit relies on the users build environemnt. I recommend installing:
* c++ build environment
* git
* mercurial
* anything a package depends on

For Ubuntu I recommend:
```bash
sudo apt-get install build-essential automake  python-pip git mercurial liblzma-dev libevent-dev ncurses-dev
```

**Github**

Fetch the latest from the source. Works unless the build badge says failing.

```bash
git clone https://github.com/starcraftman/pakit.git
cd pakit
export PATH=$(pwd)/bin:$PATH
sudo -H pip install argparse PyYAML
python setup.py release
```

**pip**

Install the latest stable pip release. It might be old but working.

```bash
sudo -H pip install pakit
```

**PATH**

By default, pakit will install programs under `paths.prefix` and link everything to `paths.link`.
To use the built programs, `paths.link`/bin must be on your $PATH.
So for example, with the default value of `paths.link`, you would need to:

```bash
export PATH=/tmp/pakit/links/bin:$PATH
```

The above exports will only last for the terminal session.
To make them permanent for bash, edit `$HOME/.bashrc` or `$HOME/.bash_aliases`.

## More Information

From inside the pakit source folder:

* Help: `pakit --help`

* Consult man: `man pakit`

* Read pydocs: `pydoc pakit` or `pydoc pakit.shell` and so on...

* Install all development packages: `python setup.py deps`

* Run the test suite: `tox`

* See [Waffle](http://waffle.io/starcraftman/pakit) for things I'm working on.

* Read `DESIGN.md` for details on design. A bit out of date.

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
- [x] Simple config from `.pakit.yml`.
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
- [x] Improve Command, timeout & input file
- [x] Investigate alternatives/improvements to RecipeDB

### 0.3
- [ ] Make a website and promote. Maybe use github pages.
- [x] Dependency logic between recipes tasks.
  - [x] Research best approach & do small design.
  - [x] Create Digraph Structure (likely required).
  - [x] Create Recipe specification & implement.
- [ ] Handle missing commands inside recipes. For example, recipe needs git but git unavailable.
- [ ] Separate recipes from pakit core.
- [ ] Move to pakit/pakit. [pakit](https://github.com/pakit)

### 0.4
- [ ] Parallelism, envisioned as some task based dependency.

### Beyond
- [ ] Create tool to convert homebrew ruby formula. Maybe?
