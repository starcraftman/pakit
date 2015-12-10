"""
Convert README.md to restructuredText for pypi description.

Depends on pandoc program and pyandoc python library.
"""
from __future__ import absolute_import, print_function

import os
import subprocess
import sys
try:
    with open(os.devnull, 'w') as dnull:
        subprocess.check_call('pandoc -v'.split(), stdout=dnull, stderr=dnull)
except OSError:
    print('Missing pandoc command. Please run:')
    print('sudo apt-get install pandoc')
    sys.exit(1)
try:
    import pandoc
except ImportError:
    print('Missing pyandoc library. Please run:')
    print('sudo -H pip install pyandoc')
    sys.exit(1)


def find_root():
    """
    Find the root of the project with README.md.
    """
    root = os.getcwd()
    while not os.path.exists(os.path.join(root, 'README.md')):
        root = os.path.basename(root)

    return root


def convert_readme(root):
    """
    Using pandoc, convert the README.md to rst.
    """
    pandoc.core.PANDOC_PATH = '/usr/bin/pandoc'
    pdoc = pandoc.Document()
    with open(os.path.join(root, 'README.md'), 'r') as fin:
        pdoc.markdown = fin.read()
    with open(os.path.join(os.getcwd(), 'README.rst'), 'w') as fout:
        fout.write(pdoc.rst)


def fix_image(readme):
    """
    Fix the embedded HTML wordmark.
    """
    with open(readme, 'r') as fin:
        lines = fin.readlines()

    with open(readme.replace('.rst', '.md'), 'r') as fin:
        html = fin.readlines()[0:4]
    html[0] = html[0].replace('#', ' ')

    lines = ['.. raw: html\n', '\n'] + html + lines

    with open(readme, 'w') as fout:
        fout.writelines(lines)


def main():
    """
    Main function.
    """
    root = find_root()
    convert_readme(root)
    readme = os.path.join(root, 'README.rst')
    fix_image(readme)

if __name__ == "__main__":
    main()
