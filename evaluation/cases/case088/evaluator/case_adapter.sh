#!/usr/bin/env bash

build_project() {
    bash -c 'python setup.py build --build-lib /testbed/build/local --build-temp /testbed/build/temp --force > /tmp/pygame-build-buffer.raw.log 2>&1; rc=$?; cat /tmp/pygame-build-buffer.raw.log; exit "$rc"' && cp lib/freesansbold.ttf /testbed/build/local/pygame/freesansbold.ttf
}

run_project_tests() {
    python /benchmark/legacy_unittest088.py \
        'test/surface_test.py::SurfaceTypeTest::test_copy' \
        'test/surface_test.py::SurfaceTypeTest::test_get_bytesize' \
        'test/surface_test.py::SurfaceTypeTest::test_get_rect' \
        'test/surface_test.py::SurfaceTypeTest::test_get_bounding_rect'
}
