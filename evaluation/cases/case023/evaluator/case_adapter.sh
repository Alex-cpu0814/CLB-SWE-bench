#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv -o markers=slow \
        'numpy/core/tests/test_multiarray.py::TestWritebackIfCopy::test_put_noncontiguous' \
        'numpy/core/tests/test_multiarray.py::TestWritebackIfCopy::test_putmask_noncontiguous' \
        'numpy/core/tests/test_multiarray.py::TestWritebackIfCopy::test_insert_noncontiguous'
}
