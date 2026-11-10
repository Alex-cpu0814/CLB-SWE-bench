"""Compatibility entry point for the CLB SWE-bench evaluation harness."""

from pathlib import Path
import sys


if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness.evaluate import main


if __name__ == "__main__":
    raise SystemExit(main())
