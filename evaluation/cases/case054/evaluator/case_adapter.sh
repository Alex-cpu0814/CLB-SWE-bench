#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'Tests/test_box_blur.py::test_radius_0' \
        'Tests/test_box_blur.py::test_radius_1' \
        'Tests/test_image_filter.py::test_invalid_box_blur_filter'
}
