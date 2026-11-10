#!/usr/bin/env bash

build_project() {
    bash -c 'python setup.py build --build-lib /testbed/build/local --build-temp /testbed/build/temp --force > /tmp/pygame-build-buffer.raw.log 2>&1; rc=$?; cat /tmp/pygame-build-buffer.raw.log; exit "$rc"'
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'test/event_test.py::EventModuleTest::test_post_large_user_event' \
        'test/event_test.py::EventModuleTest::test_get_type' \
        'test/event_test.py::EventModuleTest::test_post_blocked' \
        'test/time_test.py::TimeModuleTest::test_set_timer'
}
