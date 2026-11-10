#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    local rc=0
    python3.8-dbg -m pytest -vv \
        numpy/lib/tests/test_index_tricks.py::TestRavelUnravelIndex::test_big_indices \
        numpy/lib/tests/test_index_tricks.py::TestRavelUnravelIndex::test_dtypes \
        'numpy/lib/tests/test_index_tricks.py::TestRavelUnravelIndex::test_empty_array_ravel[clip]' || rc=$?
    python3.8-dbg -m pytest -vv \
        'numpy/lib/tests/test_index_tricks.py::TestRavelUnravelIndex::test_empty_array_ravel[wrap]' || rc=$?
    return "$rc"
}
