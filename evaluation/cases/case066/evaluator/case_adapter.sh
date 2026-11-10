#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/unittest_case066_isolated.py \
        'Tests/test_imagefont.py::TestImageFont::test_default_font' \
        'Tests/test_file_png.py::TestFilePng::test_sanity' \
        'Tests/test_font_leaks.py::TestTTypeFontLeak::test_leak' \
        'Tests/test_font_leaks.py::TestDefaultFontLeak::test_leak'
}
