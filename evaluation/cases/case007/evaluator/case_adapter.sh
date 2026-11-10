#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i
}

run_project_tests() {
    local leak_status
    local regression_status

    python3.8-dbg -m pytest -vv -R 3:3 \
        numpy/core/tests/test_multiarray.py::TestCreation::test_malloc_fails
    leak_status=$?

    python3.8-dbg -m pytest -vv \
        numpy/core/tests/test_multiarray.py::TestCreation::test_zeros
    regression_status=$?

    if [[ "${leak_status}" -ne 0 || "${regression_status}" -ne 0 ]]; then
        return 1
    fi
    return 0
}
