#!/usr/bin/env bash

build_project() {
    bash -c 'python setup.py build --build-lib /testbed/build/local --build-temp /testbed/build/temp --force > /tmp/pygame-build-buffer.raw.log 2>&1; rc=$?; cat /tmp/pygame-build-buffer.raw.log; exit "$rc"' && cp lib/freesansbold.ttf /testbed/build/local/pygame/freesansbold.ttf
}

run_project_tests() {
    bash -c 'xvfb-run -a "$@"; rc=$?; exit "$rc"' -- python /benchmark/legacy_unittest090.py \
        'test/freetype_test.py::FreeTypeFontTest::test_freetype_Font_get_rect' \
        'test/freetype_test.py::FreeTypeFontTest::test_freetype_Font_style' \
        'test/freetype_test.py::FreeTypeFontTest::test_freetype_Font_render_mono' \
        'test/freetype_test.py::FreeTypeFontTest::test_issue_242'
}
