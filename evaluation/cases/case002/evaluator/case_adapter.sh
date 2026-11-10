#!/usr/bin/env bash

# Case-specific build and test functions sourced by run_evaluation.sh.

build_project() {
    python setup.py build_ext -i
}

run_project_tests() {
    python -m pytest -vv -W ignore::DeprecationWarning \
        scipy/ndimage/tests/test_interpolation.py
}
