""" pakit: A build tool """
from __future__ import absolute_import, print_function

# Always prefer setuptools over distutils
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand
import fnmatch
import glob
import os
import pakit
import shlex
import subprocess
import sys


def get_changelog():
    """ Fetches the latest changelog for pypi """
    with open('CHANGELOG.txt') as fin:
        lines = fin.readlines()
    return '\nChange Log:\n' + ''.join(lines)


def rec_search(wildcard):
    """ Search for matching files. """
    matched = []
    for dirpath, _, files in os.walk(os.getcwd()):
        fn_files = [os.path.join(dirpath, fn_file) for fn_file
                    in fnmatch.filter(files, wildcard)]
        matched.extend(fn_files)
    return matched


class CleanCommand(Command):
    """ Equivalent of make clean """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pycs = ' '.join(rec_search('*.pyc'))
        eggs = ' '.join(glob.glob('*.egg-info'))
        cmd = 'rm -vrf .tox build dist {0} {1}'.format(eggs, pycs)
        print('Executing: ' + cmd)
        if raw_input('OK? y/n  ').strip().lower()[0] == 'y':
            subprocess.call(shlex.split(cmd))


class ReleaseCommand(Command):
    """ Prepare for twine upload by building distributions """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for cmd in ['python setup.py sdist --formats=gztar,zip',
                    'python setup.py bdist_wheel --universal']:
            subprocess.call(shlex.split(cmd))


class PyTest(TestCommand):
    """ Testing is done with py.test """
    user_options = []

    def initialize_options(self):
        self.test_suite = True
        self.test_args = []

    def finalize_options(self):
        pass

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


MY_NAME = 'Jeremy Pallats / starcraft.man'
MY_EMAIL = 'N/A'
setup(
    name='pakit',
    version=pakit.__version__,
    description='A package manager that builds from source',
    long_description=get_changelog(),
    url='https://github.com/starcraftman/pakit',
    author=MY_NAME,
    author_email=MY_EMAIL,
    maintainer=MY_NAME,
    maintainer_email=MY_EMAIL,
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Build Tools',
    ],

    # What does your project relate to?
    keywords='development',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    # packages=find_packages(exclude=['venv', 'test*']),
    packages=find_packages(exclude=['venv', 'tests*']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['argparse', 'PyYAML'],

    tests_require=['pytest', 'mock'],

    # # List additional groups of dependencies here (e.g. development
    # # dependencies). You can install these using the following syntax,
    # # for example:
    # # $ pip install -e .[dev,test]
    # extras_require={
        # 'dev': ['check-manifest'],
        # 'test': ['coverage'],
    # },

    # # If there are data files included in your packages that need to be
    # # installed, specify them here.  If using Python 2.6 or less, then these
    # # have to be included in MANIFEST.in as well.
    # package_data={
        # 'sample': ['package_data.dat'],
    # },

    # # Although 'package_data' is the preferred approach, in some case you may
    # # need to place data files outside of your packages. See:
    # # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'pakit = pakit.main:main',
        ],
    },

    cmdclass={
        'clean': CleanCommand,
        'release': ReleaseCommand,
        'test': PyTest,
    }
)
