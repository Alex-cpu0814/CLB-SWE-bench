#!/usr/bin/env bash

build_project() {
    (cd python && python setup.py build_ext --inplace)
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv \
        'python/tests/test_highlevel.py::TestTree::test_newick' \
        'python/tests/test_lowlevel.py::TestTree::test_newick_precision' \
        'python/tests/test_highlevel.py::TestTree::test_newick_large_times' \
        'python/tests/test_lowlevel.py::TestTree::test_newick_interface'
}
