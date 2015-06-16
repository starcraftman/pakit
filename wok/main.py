#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function

import os
import shutil

from formula import Ag

BUILD_DIR = '/tmp/wok/builds'

def main():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    install_dir = os.path.join(BUILD_DIR, Ag.__name__.lower())
    build = Ag(install_dir)
    build.download()
    build.build()
    assert build.verify()

if __name__ == '__main__':
    main()
