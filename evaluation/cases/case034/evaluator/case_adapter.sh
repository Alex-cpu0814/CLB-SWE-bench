#!/usr/bin/env bash

build_project() {
    python3.8 setup.py build_ext -i
}

run_project_tests() {
    python3.8 -m pytest -vv \
        'scipy/integrate/tests/test_integrate.py::test_odeint_trivial_time' \
        'scipy/integrate/tests/test_integrate.py::test_odeint_bad_shapes' \
        'scipy/integrate/tests/test_integrate.py::test_repeated_t_values'
}
