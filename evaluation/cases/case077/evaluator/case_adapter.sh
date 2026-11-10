#!/usr/bin/env bash

build_project() {
    bash -c 'python setup.py build --build-lib /testbed/build/local --build-temp /testbed/build/temp --force > /tmp/pygame-build-buffer.raw.log 2>&1; rc=$?; cat /tmp/pygame-build-buffer.raw.log; exit "$rc"'
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'test/draw_test.py::DrawRectTest::test_rect__fill' \
        'test/draw_test.py::DrawRectTest::test_rect__one_pixel_lines' \
        'test/draw_test.py::DrawRectTest::test_rect__args_without_width' \
        'test/draw_test.py::DrawRectTest::test_rect__draw_line_width'
}
