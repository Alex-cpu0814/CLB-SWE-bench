#!/usr/bin/env bash

build_project() {
    touch scipy/signal/sigtoolsmodule.c && CFLAGS="-O0 -g -fsanitize=bounds -fno-sanitize-recover=bounds" LDFLAGS="-fsanitize=bounds" python setup.py build_ext -i
}

run_project_tests() {
    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 python /benchmark/pytest_case048_isolated.py \
        'scipy/signal/tests/test_signaltools.py::TestMedFilt::test_basic' \
        'scipy/signal/tests/test_signaltools.py::TestMedFilt::test_none' \
        'scipy/signal/tests/test_signaltools.py::TestMedFilt::test_invalid_dtypes[float16]'
}
