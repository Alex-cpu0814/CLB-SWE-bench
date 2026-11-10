#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv \
        'tests/test_pattern.py::test_raster_source' \
        'tests/test_pattern.py::test_cmp_hash' \
        'tests/test_pattern.py::test_get_extend' \
        'tests/test_pattern.py::test_get_filter'
}
