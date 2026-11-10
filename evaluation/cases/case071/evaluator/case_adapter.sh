#!/usr/bin/env bash

build_project() {
    python setup.py build_ext -i --force
}

run_project_tests() {
    python /benchmark/pytest_no_dump.py -c /dev/null --rootdir=/testbed -p no:cacheprovider -vv --color=no \
        'tests/test_ujson.py::test_encode_dict_conversion' \
        'tests/test_ujson.py::test_encode_list_conversion' \
        'tests/test_ujson.py::test_decode_from_unicode' \
        'tests/test_ujson.py::test_encode_indent[{\n    "obj": 31337\n}]' \
        'tests/test_ujson.py::test_encode_indent[{}]' \
        'tests/test_ujson.py::test_encode_indent[[]]' \
        'tests/test_ujson.py::test_encode_indent[{\n    "a": {}\n}]' \
        'tests/test_ujson.py::test_encode_indent[[\n    []\n]]'
}
