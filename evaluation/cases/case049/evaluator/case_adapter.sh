#!/usr/bin/env bash

build_project() {
    python setup.py build_ext --inplace
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv \
        'Cheetah/Tests/SyntaxAndOutput.py::GetVar::test1' \
        'Cheetah/Tests/SyntaxAndOutput.py::GetVar::test2' \
        'Cheetah/Tests/SyntaxAndOutput.py::GetVar::test6'
}
