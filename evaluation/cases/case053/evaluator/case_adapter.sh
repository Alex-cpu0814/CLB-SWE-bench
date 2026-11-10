#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'Tests/test_imagedraw.py::test_sanity' \
        'Tests/test_imagefont.py::test_font_properties[Layout.BASIC]' \
        'Tests/test_imagedraw.py::test_point_I16' \
        'Tests/test_imagefont.py::test_I16[Layout.BASIC]'
}
