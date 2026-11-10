#!/usr/bin/env bash

build_project() {
    python3.8 setup.py build_ext -i
}

run_project_tests() {
    python3.8 -m pytest -c /dev/null -vv \
        'scipy/interpolate/tests/test_fitpack.py::test_dblint' \
        'scipy/interpolate/tests/test_fitpack.py::test_splev_der_k' \
        'scipy/interpolate/tests/test_fitpack.py::test_splprep_segfault'
}
