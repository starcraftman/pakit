"""
Used for pytest plugins & session scoped fixtures.
"""
from __future__ import absolute_import

import mock
import pytest
import sys
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
    if sys.version[0] == '2':
        print_mod = '__builtin__.print'
    else:
        print_mod = 'builtins.print'
    with mock.patch(print_mod) as mock_obj:
        yield mock_obj


# For puzzling problems, executes before/after each test
# @pytest.yield_fixture(scope='function', autouse=True)
# def around_all_tests():
    # """
    # Fixture sets up the testing environment for pakit as a whole.
    # """
    # # before
    # yield
    # # after
