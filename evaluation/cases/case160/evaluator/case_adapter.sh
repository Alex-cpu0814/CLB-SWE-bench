#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv -p no:warnings --hypothesis-show-statistics \
        'fast_histogram/tests/test_histogram.py::test_1d_compare_with_numpy' \
        'fast_histogram/tests/test_histogram.py::test_2d_compare_with_numpy' \
        'fast_histogram/tests/test_histogram.py::test_nd_arrays'
}
