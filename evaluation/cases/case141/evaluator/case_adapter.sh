#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv \
        'tests/test_api.py::test_context' \
        'tests/test_api.py::test_error' \
        'tests/test_api.py::test_pattern' \
        'tests/test_api.py::test_matrix'
}
