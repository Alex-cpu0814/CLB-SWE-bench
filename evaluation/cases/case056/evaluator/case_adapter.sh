#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'Tests/test_image.py::TestImage::test_fp_name' \
        'Tests/test_image.py::TestImage::test_tempfile' \
        'Tests/test_image.py::TestImage::test_pathlib'
}
