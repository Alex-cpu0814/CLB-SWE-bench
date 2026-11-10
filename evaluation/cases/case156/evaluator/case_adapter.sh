#!/usr/bin/env bash

build_project() {
    python2.7 setup.py build_ext --force build_py --force
}

run_project_tests() {
    python2.7 /benchmark/pysqlite_unittest_nodes.py \
        'lib/test/hooks.py::CollationTests::CheckCreateCollationNotCallable' \
        'lib/test/hooks.py::ProgressTests::CheckProgressHandlerUsed' \
        'lib/test/hooks.py::ProgressTests::CheckCancelOperation' \
        'lib/test/hooks.py::LimitTests::CheckGetLimit' \
        'lib/test/hooks.py::LimitTests::CheckSetLimit'
}
