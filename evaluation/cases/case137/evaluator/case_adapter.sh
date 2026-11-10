#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv \
        'tests/test_surface.py::test_surface_get_device_scale' \
        'tests/test_surface.py::test_surface_get_content' \
        'tests/test_surface.py::test_surface_get_format' \
        'tests/test_surface.py::test_surface_set_device_scale'
}
