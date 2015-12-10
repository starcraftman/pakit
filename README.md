# <a href="https://github.com/pakit"><img alt="Pakit" src="http://pakit.github.io/images/pakit-logo.png" width="16%" /></a>

[![Travis][TravisShield]][TravisDash]
[![Coveralls][CoverallsShield]][CoverallsDash]
[![Stories in Ready][WaffleShield]][WaffleDash]
[![Join Gitter Chat][GitterShield]][GitterRoom]

[![Supported Python][PyPythons]][PyPi]
[![License][PyLicense]][PyPi]
[![Version][PyVersion]][PyPi]
[![Status][PyStatus]][PyPi]

[Fork Me On Github](https://github.com/starcraftman/pakit)

## Description

Pakit is a small python based package manager that builds programs from source.

Pakit provides:

1. A package manager interface to install, remove & update programs.
1. A simple Recipe specification to build programs from source code.
1. Premade and tested [recipes][PakitRecipes] maintained by pakit.

When you install a program Pakit will...

1. download the source into a silo in `pakit.paths.source` and build it.
1. install the program into a silo under `pakit.paths.prefix`.
1. link the silo to the `pakit.paths.link` directory.

Want a longer explanation? See the [Overview][#overview] section.

## Demo

The following demonstration covers most of the basic functions.

[![Short Demo][DemoGif]][DemoText]

Try the [demo][DemoText] yourself after installing pakit.

## Install Pakit

To use pakit:

1. Ensure you have a [build enviornment][#build-env]  for compiling the programs.
1. Fetch pakit via [pip][#pip] or [github][#github].
1. Modify your [$PATH][#path].

### Build Environment

At this point pakit has two limitations to be aware of:

- Relies on user's build environment.
- Pakit recipes can only depend on things pakit can build, currently limited pool.
  User needs to install any dependencies pakit can't build.

To use pakit, I suggest you have...

- c++ build environment
- git
- anything a recipe depends on that pakit can't build

For Ubuntu install these packages:
```bash
sudo apt-get install build-essential automake autoconf python-pip git liblzma-dev libevent-dev ncurses-dev
```

### Github

Fetch the latest from the source. Works unless the build badge says failing.

```bash
git clone https://github.com/starcraftman/pakit.git
export PATH=$(pwd)/pakit/bin:$PATH
python pakit/setup.py deps release
```

### pip

Install the latest stable pip release. It might be old but working.

```bash
sudo -H pip install pakit
```

### PATH

By default, pakit will install programs under `pakit.paths.prefix`
 and link everything to `pakit.paths.link`.
To use the built programs, `pakit.paths.link`/bin must be on your $PATH.
So for example, with the default value of `pakit.paths.link`, you would need to:

```bash
export PATH=/tmp/pakit/links/bin:$PATH
```

The above exports will only last for the terminal session.
To make them permanent for bash, edit `$HOME/.bashrc` or `$HOME/.bash_aliases`.

## More Information

From inside the pakit source folder:

- Help: `pakit --help`
- Consult man: `man pakit`
- Read pydocs: `pydoc pakit` or `pydoc pakit.shell` and so on...
- Install all development packages: `python setup.py deps`
- Run the test suite: `tox`
- See [Waffle][WaffleDash] for things I'm working on.
- Read `DESIGN.md` for details on design. A bit out of date.

## Contributors

- @starcraftman/Jeremy Pallats

## Overview

Basically I want to make a universal package manager on python.
Runs everywhere, builds anything and handles dependencies.
A bit like a meta build tool tying arbitrary recipes together.
At the end of the day, will probably resemble Homebrew at least a little.

Importantly, the recipes should be configurable via a single YAML file
that users can modify without changing the recipes. Say you want to pass
particular flags to the `vim` or `ag` build, you'd just put them in an entry
in the config.

Expected Feature Overview:

- Python only, with minimal dependencies.
- Package manager interface, install remove and update recipes.
- 100% tested, framework & supported recipes.
- Should work on any POSIX system, emphasis on Linux.
- Simple recipe specification.
- Configuration via a single YAML file.
- Available via [pip][PyPi].
- Traceability via logs for every command.
- Premade & tested recipes available for use.

See the [design file][DESIGN.md] for more details.

<!-- Links -->
[TravisShield]: https://travis-ci.org/starcraftman/pakit.svg?branch=master
[TravisDash]: https://travis-ci.org/starcraftman/pakit
[CoverallsShield]: https://coveralls.io/repos/starcraftman/pakit/badge.svg?branch=master&service=github
[CoverallsDash]: https://coveralls.io/github/starcraftman/pakit
[WaffleShield]: https://badge.waffle.io/starcraftman/pakit.svg?label=ready&title=Ready
[WaffleDash]: http://waffle.io/starcraftman/pakit
[GitterShield]: https://badges.gitter.im/Join%20Chat.svg
[GitterRoom]: https://gitter.im/starcraftman/pakit?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

[PyPythons]: https://img.shields.io/pypi/pyversions/pakit.svg
[PyLicense]: https://img.shields.io/pypi/l/pakit.svg
[PyVersion]: https://img.shields.io/pypi/v/pakit.svg
[PyStatus]: https://img.shields.io/pypi/status/pakit.svg

[DemoGif]: https://github.com/pakit/demo/raw/master/demo.gif
[DemoText]: https://github.com/starcraftman/pakit/blob/master/DEMO.md#demo
[PakitRecipes]: https://github.com/pakit/base_recipes
[PyPi]: https://pypi.python.org/pypi/pakit
[DESIGN.md]: https://github.com/starcraftman/pakit/blob/master/DESIGN.md

[#overview]: https://github.com/starcraftman/pakit#overview
[#build-env]: https://github.com/starcraftman/pakit#build-environment
[#pip]: https://github.com/starcraftman/pakit#pip
[#github]: https://github.com/starcraftman/pakit#github
[#path]: https://github.com/starcraftman/pakit#path
