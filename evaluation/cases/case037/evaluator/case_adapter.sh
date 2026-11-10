#!/usr/bin/env bash

build_project() {
    python3.8 setup.py build_ext -i || return $?
    # SciPy 0.10 converts Python sources into build/py3k. NumPy 1.17
    # no longer provides the historical lazy package loader.
    sed -i '/from numpy\._import_tools import PackageLoader/,/pkgload(verbose=SCIPY_IMPORT_VERBOSE,postpone=True)/d' \
        /testbed/build/py3k/scipy/__init__.py
}

run_project_tests() {
    cd /testbed/build/py3k || return $?
    python3.8 -m pytest -vv \
        'scipy/ndimage/tests/test_regression.py::test_byte_order_median' \
        'scipy/ndimage/tests/test_regression.py::test_zoom_output_shape' \
        'scipy/ndimage/tests/test_regression.py::test_ticket_742'
}
