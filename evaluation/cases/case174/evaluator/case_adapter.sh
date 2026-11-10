#!/usr/bin/env bash

build_project() {
    cmake -S test -B build -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/opt/googletest && cmake --build build --target test_magnetic_symmetry --parallel 2
}

run_project_tests() {
    python /benchmark/native_gtest_runner.py --binary /testbed/build/test_magnetic_symmetry \
        'test/test_magnetic_symmetry.cpp::test_magnetic_symmetry.test_spg_get_magnetic_symmetry_from_database' \
        'test/test_magnetic_symmetry.cpp::test_magnetic_symmetry.test_spg_get_magnetic_spacegroup_type' \
        'test/test_magnetic_symmetry.cpp::test_magnetic_symmetry.test_spg_get_magnetic_dataset_type4' \
        'test/test_magnetic_symmetry.cpp::test_magnetic_symmetry.test_spg_get_symmetry_with_tensors_rough_mag_symprec'
}
