#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv \
        'fast_histogram/tests/test_histogram.py::test_nd_arrays' \
        'fast_histogram/tests/test_histogram.py::test_list' \
        'fast_histogram/tests/test_histogram.py::test_non_contiguous' \
        'fast_histogram/tests/test_histogram.py::test_mixed_strides'
}
