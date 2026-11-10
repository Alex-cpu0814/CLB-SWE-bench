#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'Tests/test_file_psd.py::test_sanity' \
        'Tests/test_file_psd.py::test_eoferror' \
        'Tests/test_file_psd.py::test_n_frames'
}
