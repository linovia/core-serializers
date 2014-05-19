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

def split_class_and_function(string):
    class_string, function_string = string.split('.', 1)
    return "%s and %s" % (class_string, function_string)

def is_function(string):
    return string.startswith('test_') or '.test_' in string

def is_class(string):
    return string[0] == string[0].upper()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pytest_args = sys.argv[1:]
        first_arg = pytest_args[0]
        if first_arg.startswith('-'):
            pytest_args = ['tests'] + pytest_args
        elif is_class(first_arg) and is_function(first_arg):
            expression = split_class_and_function(first_arg)
            pytest_args = ['tests', '-k', expression] + pytest_args[1:]
        elif is_class(first_arg) or is_function(first_arg):
            pytest_args = ['tests', '-k', pytest_args[0]] + pytest_args[1:]
    else:
        pytest_args = PYTEST_ARGS['default']

    exit_on_failure(pytest.main(pytest_args))
    exit_on_failure(flake8_main(FLAKE8_ARGS))
