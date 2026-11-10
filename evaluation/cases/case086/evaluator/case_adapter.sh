#!/usr/bin/env bash

build_project() {
    bash -c 'python setup.py build --build-lib /testbed/build/local --build-temp /testbed/build/temp --force > /tmp/pygame-build-buffer.raw.log 2>&1; rc=$?; cat /tmp/pygame-build-buffer.raw.log; exit "$rc"' && cp src_py/freesansbold.ttf /testbed/build/local/pygame/freesansbold.ttf
}

run_project_tests() {
    bash -c 'xvfb-run -a "$@"; rc=$?; exit "$rc"' -- python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'test/draw_test.py::DrawPolygonTest::test_draw_square' \
        'test/draw_test.py::DrawPolygonTest::test_draw_diamond' \
        'test/draw_test.py::DrawPolygonTest::test_draw_symetric_cross' \
        'test/draw_test.py::DrawPolygonTest::test_illumine_shape'
}
