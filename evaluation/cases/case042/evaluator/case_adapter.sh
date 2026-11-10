#!/usr/bin/env bash

build_project() {
    python3.8 setup.py build_ext -i
}

run_project_tests() {
    python3.8 -m pytest -c /dev/null -vv \
        'scipy/signal/tests/test_bsplines.py::TestBSplines::test_spline_filter' \
        'scipy/signal/tests/test_bsplines.py::TestBSplines::test_bspline' \
        'scipy/signal/tests/test_bsplines.py::test_sepfir2d_invalid_filter'
}
