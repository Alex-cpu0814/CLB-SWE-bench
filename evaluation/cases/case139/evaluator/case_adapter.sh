#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -vv \
        'tests/test_device.py::test_get_device' \
        'tests/test_surface.py::test_script_surface' \
        'tests/test_surface.py::test_script_surface_create_for_target' \
        'tests/test_surface.py::test_script_device_device_ref'
}
