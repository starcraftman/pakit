# PakIt

[![Travis](https://img.shields.io/travis/starcraftman/pakit/master.svg)](https://travis-ci.org/starcraftman/pakit) 
[![Coveralls](https://coveralls.io/repos/starcraftman/pakit/badge.svg?branch=master&service=github)](https://coveralls.io/github/starcraftman/pakit?branch=master)

[![Python](https://img.shields.io/pypi/pyversions/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![License](https://img.shields.io/pypi/l/Django.svg)](https://pypi.python.org/pypi/pakit)
[![Version](https://img.shields.io/pypi/v/pakit.svg)](https://pypi.python.org/pypi/pakit)
[![Status](https://img.shields.io/pypi/status/pakit.svg)](https://pypi.python.org/pypi/pakit)

[![Join the chat at https://gitter.im/starcraftman/pakit](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/pakit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## Motivation
Should be something like homebrew when done. Why? Why not.

Expected Features:
* Python only.
* Should work on any posix system, emphasis on Linux.
* Simple recipe specification.
* Config via single YAML file.
* Available via pip & wheel eventually.

## Roadmap
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
- [ ] Add archive support, supports download, hashing & extracting.
  - [ ] Tar (tarfile)
  - [ ] Zip (zipfile)
  - [ ] tar.xz (cmdline)
  - [ ] Rar (cmdline?)
- [ ] Add list & searching support.
- [ ] Investigate alternatives to RecipeDB
- [ ] Python 3 support?

### 0.3
- [ ] Dependency logic between recipes tasks.

### 0.4
- [ ] Parallelism, envisioned as some task based dependency.

### Beyond
- [ ] Make an organization.
- [ ] Formulas go to separate repo.
- [ ] Create tool to convert homebrew ruby formula. Maybe?
- [ ] Make a simple io website & promote?
