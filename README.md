# wok

[![travis-ci](https://travis-ci.org/starcraftman/wok.svg?branch=master)](https://travis-ci.org/starcraftman/wok) [![Join the chat at https://gitter.im/starcraftman/wok](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/wok?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Goal:
* A python like homebrew application for posix systems.
* Easy to write recipes for, keep them small.
* Should be simple to use/modify.
* Available from pip/wheel.

# Roadmap
Just a rough guess of what I should be implementing when.

### 0.1
- [x] Implement basic tasks to install & remove 'ag' program.
- [x] Support Git & Hg repositories.
- [x] Simple config from `.wok.yml`.
- [ ] Upgrade logic.
- [ ] Pick a license.

### 0.2
- [ ] Add archive support, supports download, hashing & extracting.
  - [ ] Tar (tarfile)
  - [ ] Zip (zipfile)
  - [ ] tar.xz (cmdline)
  - [ ] Rar (cmdline?)
- [ ] Add list/searching support.
- [ ] Test alternative recipe approaches for scaling.
- [ ] User defined recipes via config.

### 0.3
- [ ] Add dependency logic, so one recipe can depend on another.

### 0.4
- [ ] Parallelism, envisioned as some task based dependency.

### Beyond
- [ ] Make an organization.
- [ ] Formulas go to separate repo.
- [ ] Create tool to convert homebrew ruby formula.
- [ ] Make a simple io website & promote?
- [ ] Contributors?
