#! /usr/bin/env python
import pytest
import sys
import os
import subprocess


PYTEST_ARGS = {
    'default': ['tests', '--cov', 'core_serializers', '--cov', 'tests', '--cov-report', 'term', '--cov-report', 'html'],
    'nocov': ['tests',],
    'travis': ['tests', '--cov', 'core_serializers', '--cov', 'tests', '--cov-report', 'term', '-v']
}

FLAKE8_ARGS = {
    'default': ['core_serializers', 'tests', '--ignore=E501'],
    'nocov': ['core_serializers', 'tests', '--ignore=E501'],
    'travis': ['core_serializers', 'tests', '--ignore=E501'],
}

sys.path.append(os.path.dirname(__file__))

def exit_on_failure(ret):
    if ret:
        sys.exit(ret)

def flake8_main(args):
    return subprocess.call(['flake8'] + args)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in PYTEST_ARGS.keys():
        style = sys.argv[1]
        custom_args = sys.argv[2:]
    else:
        style = 'default'
        custom_args = sys.argv[1:]
    exit_on_failure(pytest.main(PYTEST_ARGS[style] + custom_args))
    if FLAKE8_ARGS[style] is not None:
        exit_on_failure(flake8_main(FLAKE8_ARGS[style]))
