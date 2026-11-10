#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv \
        numpy/core/tests/test_multiarray.py::TestMethods::test_searchsorted \
        numpy/core/tests/test_multiarray.py::TestMethods::test_searchsorted_unicode \
        numpy/core/tests/test_multiarray.py::TestMethods::test_searchsorted_with_sorter
}
