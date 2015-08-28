# PakIt

[![Travis](https://travis-ci.org/starcraftman/pakit.svg?branch=master)](https://travis-ci.org/starcraftman/pakit)
[![Coveralls](https://coveralls.io/repos/starcraftman/pakit/badge.svg?branch=master&service=github)](https://coveralls.io/github/starcraftman/pakit?branch=master)
[![Stories in Ready](https://badge.waffle.io/starcraftman/pakit.svg?label=ready&title=Ready)](http://waffle.io/starcraftman/pakit)
[![Join the chat at https://gitter.im/starcraftman/pakit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/pakit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Python](https://img.shields.io/pypi/pyversions/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![License](https://img.shields.io/pypi/l/Django.svg)](https://pypi.python.org/pypi/pakit)
[![Version](https://img.shields.io/pypi/v/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![Status](https://img.shields.io/pypi/status/pakit.svg)](https://pypi.python.org/pypi/pakit)

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
  - [ ] tar.xz (cmdline)
  - [ ] Rar (cmdline?)
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
