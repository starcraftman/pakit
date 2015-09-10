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

It is a small, python based package manager that builds from source.

Want a longer explanation? Skip to the [Overview](https://github.com/starcraftman/pakit#overview) section.

## Install Pakit

To install pakit, use the **pip** or the **Github** method. Then modify your **PATH**.

**Github**

Fetch the latest from the source. Works unless the build badge says failing.

```bash
git clone https://github.com/starcraftman/pakit.git
export PATH=$(pwd)/pakit/bin:$PATH
sudo pip install argparse PyYAML
```

**pip**

Install the latest stable pip release. It might be old but working.

```bash
sudo pip install pakit
```

**PATH**

By default, pakit will install programs into `paths.prefix`.
The default value is: `/tmp/pakit/links`.
So all binaries will be in: `/tmp/pakit/links/bin`.
To use the built programs you must put them on your $PATH.

```bash
export PATH=/tmp/pakit/links/bin:$PATH
```

The above exports will only last for the terminal session.
To make them permanent for bash, edit `~/.bashrc` or `~/.bash_aliases`.

## Try Pakit In 5 Minutes

After having installed PakIt, try a simple demo.

![PakIt Demo](http://cdn.makeagif.com/media/9-08-2015/-3StlV.gif)

### [FOR DEMO STEPS CLICK HERE](https://github.com/starcraftman/pakit/blob/master/DEMO.md#demo)

## More Information

From inside the pakit source folder:

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
- [x] Improve Command, timeout & input file
- [x] Investigate alternatives/improvements to RecipeDB

### 0.3
- [ ] Make a website and promote. Maybe use github pages.
- [ ] Dependency logic between recipes tasks.
  - [ ] Research best approach & do small design.
  - [ ] Create Digraph Structure (likely required).
  - [ ] Create Recipe specification & implement.
  - [ ] Create ready/blocked task lists. Tasks blocked unless dependencies resolved.
- [ ] Handle missing commands inside recipes. For example, recipe needs git but git unavailable.
- [ ] Separate recipes from pakit core.
- [ ] Move to pakit/pakit. [pakit](https://github.com/pakit)

### 0.4
- [ ] Parallelism, envisioned as some task based dependency.

### Beyond
- [ ] Create tool to convert homebrew ruby formula. Maybe?
