#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_case060_isolated.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'Tests/test_image.py::TestImage::test_linear_gradient_wrong_mode' \
        'Tests/test_image.py::TestImage::test_radial_gradient_wrong_mode' \
        'Tests/test_image.py::TestImage::test_linear_gradient' \
        'Tests/test_image.py::TestImage::test_radial_gradient'
}
