#!/usr/bin/env bash

build_project() {
    python3.8-dbg setup.py build_ext -i --force
}

run_project_tests() {
    python3.8-dbg -m pytest -vv -o markers=slow \
        'numpy/core/tests/test_multiarray.py::test_interface_no_shape' \
        'numpy/core/tests/test_multiarray.py::test_array_interface_itemsize' \
        'numpy/core/tests/test_multiarray.py::TestArrayInterface::test_scalar_interface[val6-iface6-ValueError]' \
        'numpy/core/tests/test_multiarray.py::TestArrayInterface::test_scalar_interface[val8-iface8-ValueError]' \
        'numpy/core/tests/test_multiarray.py::TestArrayInterface::test_scalar_interface[val9-iface9-TypeError]'
}
