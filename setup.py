"""
The setup file for packaging pakit
"""
from __future__ import absolute_import, print_function

import fnmatch
import glob
import os
import shlex
import shutil
import subprocess
import sys
from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand

ROOT = os.path.abspath(os.path.dirname(__file__))
if os.path.dirname(__file__) == '':
    ROOT = os.getcwd()


def get_version():
    """
    Read version from source code.
    """
    v_line = None
    with open(os.path.join(ROOT, 'pakit', '__init__.py')) as fin:
        for line in fin:
            if line.find('__version__') == 0:
                v_line = line
                break

    return v_line.split()[2].replace("'", '', 2)


def get_short_desc():
    """
    Fetch one line description from pakit's code.
    """
    with open(os.path.join(ROOT, 'pakit', '__init__.py')) as fin:
        d_line = fin.readlines()[1]
    return d_line.split(':')[1].strip()


def get_long_desc():
    """
    Creates a long description for pypi.
    If possible, by converting the README.md with pandoc.
    """
    rst_file = os.path.join(os.getcwd(), 'README.rst')
    try:
        subprocess.check_call(['python', './docs/pand.py'])
        with open(rst_file) as fin:
            lines = fin.readlines()
        return '\n' + ''.join(lines)
    except subprocess.CalledProcessError:
        return '\nFor more information: https://github.com/starcraftman/pakit'
    finally:
        try:
            os.remove(rst_file)
        except OSError:
            pass


def rec_search(wildcard):
    """
    Traverse all subfolders and match files against the wildcard.

    Returns:
        A list of all matching files absolute paths.
    """
    matched = []
    for dirpath, _, files in os.walk(os.getcwd()):
        fn_files = [os.path.join(dirpath, fn_file) for fn_file
                    in fnmatch.filter(files, wildcard)]
        matched.extend(fn_files)
    return matched


class CleanCommand(Command):
    """
    Equivalent of make clean.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pycs = ' '.join(rec_search('*.pyc'))
        eggs = ' '.join(glob.glob('*.egg-info') + glob.glob('*.egg'))
        cmd = 'rm -vrf .eggs .tox build dist {0} {1}'.format(eggs, pycs)
        print('Executing: ' + cmd)
        if raw_input('OK? y/n  ').strip().lower()[0] == 'y':
            subprocess.call(shlex.split(cmd))


class ReleaseCommand(Command):
    """
    Prepare for twine upload by building distributions.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        old_cwd = os.getcwd()
        os.chdir(os.path.join(ROOT, 'docs'))
        try:
            subprocess.check_call(shlex.split('make man'))
        except OSError:
            print('Please install GNU Make.')
            sys.exit(1)

        os.chdir(ROOT)
        self.copy_files_to(os.path.join('pakit', 'extra'))

        cmds = [
            'python setup.py sdist --formats=gztar,zip',
            'python setup.py bdist_wheel --universal',
        ]
        for cmd in cmds:
            subprocess.call(shlex.split(cmd))

        os.chdir(old_cwd)

    def copy_files_to(self, target):
        """
        Copy some files into the package for distribution.
        """
        man_dir = os.path.join('docs', '_build', 'man')
        to_move = ['CHANGELOG', 'DEMO.md', 'LICENSE', 'README.md'] + \
                  [os.path.join(man_dir, man) for man in os.listdir(man_dir)]

        try:
            shutil.rmtree(target)
        except OSError:
            pass
        try:
            os.makedirs(target)
        except OSError:
            pass
        for fname in to_move:
            shutil.copy(fname, target)
        shutil.copytree('completion', os.path.join(target, 'completion'))


class InstallDeps(Command):
    """
    Install dependencies to run & test.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print('Installing runtime & testing dependencies')
        cmd = 'sudo -H pip install ' + ' '.join(RUN_DEPS + TEST_DEPS)
        print('Will execute: ' + cmd)
        subprocess.call(shlex.split(cmd))


class PyTest(TestCommand):
    """
    Testing is done with py.test
    """
    user_options = []

    def initialize_options(self):
        self.test_suite = True
        self.test_args = []

    def finalize_options(self):
        pass

    def run_tests(self):
        try:
            import pytest
            sys.exit(pytest.main(self.test_args))
        except ImportError:
            print('Missing dependencies. Execute:')
            print('  python setup.py deps')
            sys.exit(1)


MY_NAME = 'Jeremy Pallats / starcraft.man'
MY_EMAIL = 'N/A'
RUN_DEPS = ['argparse', 'pyyaml']
TEST_DEPS = ['coverage', 'flake8', 'mock', 'pytest', 'sphinx', 'tox']
setup(
    name='pakit',
    version=get_version(),
    description=get_short_desc(),
    long_description=get_long_desc(),
    url='https://github.com/starcraftman/pakit',
    author=MY_NAME,
    author_email=MY_EMAIL,
    maintainer=MY_NAME,
    maintainer_email=MY_EMAIL,
    license='BSD',
    platforms=['any'],

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Installation/Setup',
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
    install_requires=RUN_DEPS,

    tests_require=TEST_DEPS,

    # # List additional groups of dependencies here (e.g. development
    # # dependencies). You can install these using the following syntax,
    # # for example:
    # # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['pyandoc'],
        'test': TEST_DEPS,
    },

    # # If there are data files included in your packages that need to be
    # # installed, specify them here.  If using Python 2.6 or less, then these
    # # have to be included in MANIFEST.in as well.
    package_data={
        'pakit': ['extra/CHANGELOG', 'extra/DEMO.md', 'extra/LICENSE',
                  'extra/README.md', 'extra/pakit.1',
                  'extra/completion/pakit-bash.sh',
                  'extra/completion/README.md'],
    },

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
        'deps': InstallDeps,
        'release': ReleaseCommand,
        'test': PyTest,
    }
)
