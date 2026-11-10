#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv \
        'numpy/core/tests/test_dtype.py::TestRecord::test_partial_dict' \
        'numpy/core/tests/test_dtype.py::TestSubarray::test_single_subarray' \
        'numpy/core/tests/test_dtype.py::TestRecord::test_fieldless_views'
}
