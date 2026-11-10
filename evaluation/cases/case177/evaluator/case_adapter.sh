#!/usr/bin/env bash

build_project() {
    python2.7 setup.py clean build_ext --inplace --force && mkdir -p target/test-classes && javac -d target/test-classes src/main/java/org/jpy/annotations/*.java src/test/java/org/jpy/fixtures/*.java
}

run_project_tests() {
    python2.7 /benchmark/unittest_native_runner.py \
        'src/test/python/jpy_overload_test.py::TestMethodOverloads::test_2ArgOverloadsWithVaryingTypes' \
        'src/test/python/jpy_overload_test.py::TestMethodOverloads::test_nArgOverloads' \
        'src/test/python/jpy_overload_test.py::TestMethodOverloads::test_nArgOverloadsAreFoundInBaseClass' \
        'src/test/python/jpy_overload_test.py::TestStaticMethodOverloads::test_staticMethodIsFoundOverNonStatic'
}
