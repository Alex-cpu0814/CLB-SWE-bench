#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv \
        'numpy/core/tests/test_regression.py::TestRegression::test_lexsort' \
        'numpy/core/tests/test_regression.py::TestRegression::test_lexsort_invalid_sequence' \
        'numpy/core/tests/test_regression.py::TestRegression::test_lexsort_zerolen_custom_strides' \
        'numpy/core/tests/test_regression.py::TestRegression::test_lexsort_zerolen_custom_strides_2d'
}
