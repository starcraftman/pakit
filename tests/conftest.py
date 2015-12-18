"""
Used for pytest plugins & session scoped fixtures.
"""
from __future__ import absolute_import
import sys
import mock
import pytest

import tests.common as tc


@pytest.fixture(scope='session', autouse=True)
def setup_test_bed(request):
    """
    Fixture sets up the testing environment for pakit as a whole.

    Session scope, executes before all tests.
    """
    request.addfinalizer(tc.env_teardown)
    tc.env_setup()


@pytest.yield_fixture()
def mock_print():
    """
    A fixture that mocks python's print function during test.
    """
    if sys.version_info < (3, 0):
        print_mod = '__builtin__.print'
    else:
        print_mod = 'builtins.print'
    with mock.patch(print_mod) as mock_obj:
        yield mock_obj


@pytest.yield_fixture()
def mock_input():
    """
    A fixture that mocks python's print function during test.
    """
    if sys.version_info < (3, 0):
        input_mod = '__builtin__.raw_input'
    else:
        input_mod = 'builtins.input'
    with mock.patch(input_mod) as mock_obj:
        yield mock_obj


@pytest.yield_fixture(scope='function', autouse=True)
def around_all_tests():
    """
    Executes before and after EVERY test.

    Can be helpful for tracking bugs impacting test bed.
    """
    # before
    yield
    # after
