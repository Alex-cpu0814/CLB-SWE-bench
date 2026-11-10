#!/usr/bin/env python3
"""Select this case’s test-log parser and evaluation profile."""

from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from harness.case_evaluator import evaluate_case, normalize_status
finally:
    sys.path.pop(0)


TEST_LINE = re.compile(
    r"^(?P<method>\S+) \((?P<class>[^)]+)\) \.\.\. "
    r"(?P<status>ok|FAIL|ERROR|skipped(?: .*)?)$"
)
TEST_START_LINE = re.compile(r"^(?P<method>\S+) \((?P<class>[^)]+)\) \.\.\. .*")
PYTEST_LINE = re.compile(
    r"^(?P<test_id>Tests/\S+)\s+"
    r"(?P<status>PASSED|FAILED|ERROR|SKIPPED)(?:\s+\[.*\])?$"
)


def parse_test_log(text):
    statuses = {}
    pending = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        pytest_match = PYTEST_LINE.match(line)
        if pytest_match:
            statuses[pytest_match.group("test_id")] = pytest_match.group("status")
            pending = None
            continue
        match = TEST_LINE.match(line)
        if not match:
            if pending and (line in ("ok", "FAIL", "ERROR") or line.startswith("skipped")):
                statuses[pending] = normalize_status(line)
                pending = None
                continue
            start = TEST_START_LINE.match(line)
            if start:
                pending = "{}.{}".format(start.group("class"), start.group("method"))
            continue
        test_id = "{}.{}".format(match.group("class"), match.group("method"))
        statuses[test_id] = normalize_status(match.group("status"))
    return statuses


def main(argv=None):
    return evaluate_case(
        __file__, parse_test_log, argv,
        python_c=True,
        configured_docker_args=True,
    )


if __name__ == "__main__":
    sys.exit(main())
