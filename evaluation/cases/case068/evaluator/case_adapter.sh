#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/tester_case068_isolated.py \
        'Tests/test_image_convert.py::test_default' \
        'Tests/test_image_convert.py::test_8bit' \
        'Tests/test_image_quantize.py::test_octree_quantize' \
        'Tests/test_image_convert.py::test_rgba_p' \
        'Tests/test_image_convert.py::test_trns_p' \
        'Tests/test_image_convert.py::test_trns_l' \
        'Tests/test_image_convert.py::test_trns_RGB' \
        'Tests/test_image_quantize.py::test_rgba_quantize'
}
