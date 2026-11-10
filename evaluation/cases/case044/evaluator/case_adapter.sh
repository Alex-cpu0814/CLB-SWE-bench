#!/usr/bin/env bash

build_project() {
    python3.6 setup.py build_ext -i
}

run_project_tests() {
    python3.6 -m pytest -c /dev/null -vv \
        'scipy/ndimage/tests/test_ndimage.py::TestNdimage::test_map_coordinates01' \
        'scipy/ndimage/tests/test_ndimage.py::TestNdimage::test_map_coordinates02' \
        'scipy/ndimage/tests/test_ndimage.py::TestNdimage::test_map_coordinates_large_data'
}
