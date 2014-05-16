#! /usr/bin/env python
import pytest
import sys
import os
import subprocess


PYTEST_ARGS = {
    'default': ['tests', '--cov', 'core_serializers', '--cov', 'tests', '--cov-report', 'term', '--cov-report', 'html'],
    'travis': ['tests', '--cov', 'core_serializers', '--cov', 'tests', '--cov-report', 'term', '-v']
}

FLAKE8_ARGS = ['core_serializers', 'tests', '--ignore=E501']


sys.path.append(os.path.dirname(__file__))

def exit_on_failure(ret):
    if ret:
        sys.exit(ret)

def flake8_main(args):
    return subprocess.call(['flake8'] + args)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pytest_args = sys.argv[1:]
        if not pytest_args or pytest_args[0].startswith('-'):
            pytest_args = ['tests'] + pytest_args
    else:
        pytest_args = PYTEST_ARGS['default']

    exit_on_failure(pytest.main(pytest_args))
    exit_on_failure(flake8_main(FLAKE8_ARGS))
