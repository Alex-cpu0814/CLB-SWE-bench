#!/usr/bin/env bash

build_project() {
    sed -i '5i from distutils.errors import DistutilsExecError' numpy/distutils/ccompiler.py
    python2.7 setup.py build_ext -i --force
}

run_project_tests() {
    python2.7 -m nose -v \
        'numpy/core/tests/test_multiarray.py:TestChoose.test_basic' \
        'numpy/core/tests/test_multiarray.py:TestChoose.test_broadcast1' \
        'numpy/core/tests/test_multiarray.py:TestChoose.test_broadcast2'
}
