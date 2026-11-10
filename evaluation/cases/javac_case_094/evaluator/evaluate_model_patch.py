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


def parse_test_log(text):
    statuses = {}
    pending = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = TEST_LINE.match(line)
        if not match:
            if pending and (line in ("ok", "FAIL", "ERROR") or line.startswith("skipped")):
                statuses[pending] = normalize_status(line)
                pending = None
                continue
            start = TEST_START_LINE.match(line)
            if start:
                pending = "{}.{}".format(start.group("class"), start.group("method"))
                if pending.startswith("tests."):
                    pending = pending[len("tests."):]
            continue
        test_id = "{}.{}".format(match.group("class"), match.group("method"))
        if test_id.startswith("tests."):
            test_id = test_id[len("tests."):]
        statuses[test_id] = normalize_status(match.group("status"))
    return statuses


def main(argv=None):
    return evaluate_case(__file__, parse_test_log, argv)


if __name__ == "__main__":
    sys.exit(main())
