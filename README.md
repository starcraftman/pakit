# wok

[![travis-ci](https://travis-ci.org/starcraftman/wok.svg?branch=master)](https://travis-ci.org/starcraftman/wok) [![Coverage Status](https://coveralls.io/repos/starcraftman/wok/badge.svg?branch=coverage&service=github)](https://coveralls.io/github/starcraftman/wok?branch=master) [![Join the chat at https://gitter.im/starcraftman/wok](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/wok?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

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
- [x] Simple config from `.wok.yml`.
- [ ] Upgrade logic.
- [ ] User defined recipe locations via config.
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
