# wok [![travis-ci](https://travis-ci.org/starcraftman/wok.svg?branch=master)](https://travis-ci.org/starcraftman/wok)
---------

[![Join the chat at https://gitter.im/starcraftman/wok](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/starcraftman/wok?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Goal:
* A python like homebrew application for posix systems.
* Easy to write recipes for, keep them small.
* Should be simple to use/modify.
* Available from pip/wheel.

# Roadmap
Just a rough guess of what I should be implementing when.

### 0.1
* Complete example to install/remove ag.
* Upgrading logic & caching (i.e. don't rebuild if latest).
* Simple config from `.wok.yml`.

### 0.2
* Add archive support & other VCS.
* Add list/searching support.
* Figure out how to scale recipes well.

### 0.3 
* Add dependency logic, so one recipe can depend on another.

### 0.4
* Parallelism, ability to install/upgrade in parallel.

### Beyond
* Make an organization.
* Formulas go to separate repo.
* Create tool to convert homebrew ruby formula.
* Make a simple io website & promote?
* Find a helper? If you are interested, make an issue & ping me.
