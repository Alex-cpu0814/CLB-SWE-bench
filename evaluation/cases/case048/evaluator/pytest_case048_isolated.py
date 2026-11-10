"""Run each official pytest node separately, preserving fatal sanitizer diagnostics."""
import os
import re
import subprocess
import sys


def main():
    failures = 0
    for node in sys.argv[1:]:
        print("BENCHMARK_NODE_START " + node, flush=True)
        command = [sys.executable, "/benchmark/pytest_no_dump.py", "-c", "/dev/null",
                   "--rootdir=/testbed", "-p", "no:cacheprovider", "-vv", "-s", node]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=os.environ.copy())
        output = result.stdout.decode("utf-8", errors="replace")
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
        # A zero exit alone cannot establish that the expected node ran and passed.
        passed = result.returncode == 0 and re.search(
            r"^" + re.escape(node) + r"\s+PASSED(?:\s+\[.*\])?$", output, re.MULTILINE)
        status = "PASSED" if passed else "FAILED"
        print("BENCHMARK_NODE_EXIT {} {}".format(node, result.returncode), flush=True)
        print("{} {}".format(node, status), flush=True)
        failures += not passed
    return int(bool(failures))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("At least one official pytest node is required")
    sys.exit(main())
