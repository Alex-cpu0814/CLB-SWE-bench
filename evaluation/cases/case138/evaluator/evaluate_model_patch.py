#!/usr/bin/env python3
"""Select this case’s test-log parser and evaluation profile."""

from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from harness.case_evaluator import evaluate_case
finally:
    sys.path.pop(0)


TEST_LINE = re.compile(
    r"^(?P<method>\S+) \((?P<class>[^)]+)\) \.\.\. "
    r"(?P<status>ok|FAIL|ERROR|skipped(?: .*)?)$"
)
TEST_START_LINE = re.compile(r"^(?P<method>\S+) \((?P<class>[^)]+)\) \.\.\. .*")
PYTEST_LINE = re.compile(
    r"^(?P<test_id>tests/\S+)\s+"
    r"(?P<status>PASSED|FAILED|ERROR|SKIPPED)(?:\s+\[.*\])?$"
)


def parse_test_log(text):
    # Official wrapper owns terminal statuses after checking true child results.
    # Human-readable bundled-unittest output is retained but is not a second ID.
    statuses = {}
    for line in text.splitlines():
        match = PYTEST_LINE.fullmatch(line)
        if match:
            statuses[match.group("test_id")] = match.group("status")
    return statuses


def main(argv=None):
    return evaluate_case(
        __file__, parse_test_log, argv,
        python_c=True,
        configured_docker_args=True,
    )


if __name__ == "__main__":
    sys.exit(main())
