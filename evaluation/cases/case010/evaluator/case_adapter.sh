#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv \
        numpy/core/tests/test_multiarray.py::TestMethods::test_choose \
        numpy/core/tests/test_multiarray.py::TestMethods::test_round \
        numpy/core/tests/test_multiarray.py::TestMethods::test_trace \
        numpy/core/tests/test_multiarray.py::TestArgmax::test_ret_is_out \
        numpy/core/tests/test_multiarray.py::TestArgmin::test_ret_is_out \
        numpy/core/tests/test_multiarray.py::TestTake::test_ret_is_out \
        numpy/core/tests/test_multiarray.py::TestTake::test_clip \
        numpy/core/tests/test_multiarray.py::TestArgmax::test_output_shape \
        numpy/core/tests/test_multiarray.py::TestMethods::test_trace_subclass
}
