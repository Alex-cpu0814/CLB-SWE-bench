"""Run original MemoryUtil API and native allocator controls in isolated JVMs."""
import json
from pathlib import Path
import subprocess
import sys
import shutil
from upstream_results import parse_upstream_results


repo = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
if repo != Path("/testbed") or out != Path("/results"):
    raise SystemExit("Unexpected evaluation paths")

classes = str(repo / "bin/Core") + ":" + str(repo / "bin/Regression")
tests = {}
for mode in ("nullBufferNoOp", "mallocFree", "callocFree", "reallocNullFree",
             "unknownPointerRejected", "bufferFree"):
    command = [
        "java", "-Djava.library.path=" + str(repo / "libs"),
        "-Dorg.lwjgl.system.allocator=system",
        "-Dorg.lwjgl.util.DebugAllocator=true",
        "-XX:ErrorFile=" + str(out / "hs_err-%p.log"),
        "-cp", classes, "org.lwjgl.system.OriginalApiRegressionTest", mode,
    ]
    with (out / (mode + ".private.log")).open("wb") as log:
        try:
            result = subprocess.run(command, cwd=repo, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=60)
        except subprocess.TimeoutExpired:
            print(json.dumps({"phase": "runtime", "infrastructure_error": True,
                              "reason": "timeout", "tests": tests}))
            raise SystemExit(2)
    status = "passed" if result.returncode == 0 else "failed" if result.returncode == 1 else "error"
    tests["org.lwjgl.system.OriginalApiRegressionTest::" + mode] = {
        "status": status, "exit_code": result.returncode,
    }

# The original Ant task may exit zero even when TestNG has failures.
manifest = json.loads(Path("/benchmark/upstream_tests.json").read_text())
xml = repo / "bin/HTML/tests/testng-results.xml"
if xml.exists():
    xml.unlink()
with (out / "upstream-tests.private.log").open("wb") as log:
    try:
        upstream = subprocess.run([
            "ant", "-noinput", "-Dbuild.offline=true",
            "-Djvmargs=-Dorg.lwjgl.system.allocator=system -XX:ErrorFile=/results/upstream-hs_err-%p.log",
            "tests",
        ], cwd=repo, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        upstream_exit = upstream.returncode
    except subprocess.TimeoutExpired:
        upstream_exit = -1
upstream_tests, upstream_details, upstream_ok = parse_upstream_results(
    xml, manifest["test_ids"], upstream_exit)
if xml.is_file():
    shutil.copyfile(xml, out / "upstream-testng-results.xml")
tests.update(upstream_tests)
(out / "upstream-suite.json").write_text(json.dumps(upstream_details, indent=2) + "\n")
report = {"oracle_type": "runtime_behavior", "phase": "runtime",
          "upstream_suite": upstream_details, "upstream_suite_passed": upstream_ok,
          "infrastructure_error": any(item["status"] == "error" for item in tests.values()),
          "tests": tests}
(out / "sanitized_results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
raise SystemExit(2 if report["infrastructure_error"] else
                 0 if upstream_ok and all(item["status"] == "passed" for item in tests.values()) else 1)
