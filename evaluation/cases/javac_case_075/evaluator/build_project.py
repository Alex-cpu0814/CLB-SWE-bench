"""Build candidate sources with the original complete Ant/Kotlin/JNI targets."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/testbed").resolve()
if repo != Path("/testbed") or not (repo / "build.xml").is_file():
    raise SystemExit("Expected isolated /testbed LWJGL checkout")

manifest = json.loads(Path("/benchmark/upstream_tests.json").read_text())
for relative, digest in manifest["source_sha256"].items():
    if hashlib.sha256((repo / relative).read_bytes()).hexdigest() != digest:
        raise SystemExit("Protected upstream test changed: " + relative)
deps = Path("/benchmark/dependencies")
libs = repo / "libs"
libs.mkdir(exist_ok=True)
for name in ("jcommander.jar", "testng.jar"):
    shutil.copyfile(deps / name, libs / name)
shutil.copytree(deps / "kotlinc", libs / "kotlinc", dirs_exist_ok=True)
(libs / "touch.txt").touch()
(libs / "linux/x64").mkdir(parents=True, exist_ok=True)
shutil.copyfile("/usr/lib/x86_64-linux-gnu/libffi.a", libs / "linux/x64/libffi.a")
command = ["ant", "-noinput", "-Dbuild.offline=true", "compile-templates",
           "compile-native", "compile-tests"]
print(json.dumps({"phase": "full_ant_build", "command": command}), flush=True)
result = subprocess.run(command, cwd=repo)
if result.returncode:
    raise SystemExit(result.returncode)
test = repo / "config/tests/case075/org/lwjgl/system/OriginalApiRegressionTest.java"
classes = repo / "bin/Regression"
classes.mkdir(parents=True, exist_ok=True)
raise SystemExit(subprocess.run([
    "javac", "-source", "8", "-target", "8", "-encoding", "UTF-8",
    "-cp", str(repo / "bin/Core"), "-d", str(classes), str(test),
], cwd=repo).returncode)
