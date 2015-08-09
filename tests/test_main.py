""" To be used at some point. Maybe?"""
from __future__ import absolute_import, print_function

import os
import pytest
import shutil
import sys

#from wok.conf import Config
#from wok.recipe import *
#from wok.shell import *
#from wok.task import *
from wok.main import main, parse_tasks

def test_main_no_args():
    """ Test parsing by stubbing argv. """
    pass
