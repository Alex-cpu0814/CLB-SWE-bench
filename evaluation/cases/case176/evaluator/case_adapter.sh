#!/usr/bin/env bash

build_project() {
    python2.7 setup.py clean build_ext --inplace --force && mkdir -p target/test-classes && javac -d target/test-classes src/main/java/org/jpy/annotations/*.java src/test/java/org/jpy/fixtures/*.java
}

run_project_tests() {
    python2.7 /benchmark/unittest_native_runner.py \
        'src/test/python/jpy_array_test.py::TestJavaArrays::test_array_int' \
        'src/test/python/jpy_array_test.py::TestJavaArrays::test_array_object' \
        'src/test/python/jpy_array_test.py::TestJavaArrays::test_buffer_int' \
        'src/test/python/jpy_array_test.py::TestJavaArrays::test_array_item_del'
}
