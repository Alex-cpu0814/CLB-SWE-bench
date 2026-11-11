"""Audit one CLB Base image before running an agent or publishing the image."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness.runtime import checked_file, load_index, read_json


COMMIT = re.compile(r"[0-9a-f]{40}")
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
PINNED_REFERENCE = re.compile(r"[^@\s]+@sha256:[0-9a-f]{64}")

PROBE = r"""
set -euo pipefail
export LC_ALL=C
cd /testbed
test "$(git rev-parse --show-toplevel)" = "$(pwd -P)"
head=$(git rev-parse --verify HEAD)
tree=$(git rev-parse --verify 'HEAD^{tree}')
commit_count=$(git rev-list --count HEAD --all)
shallow=$(git rev-parse --is-shallow-repository)
object=$(printf '%s\n' "$1" | git cat-file --batch-check='%(objecttype)')
case "$object" in
    commit) fix_object=true ;;
    "$1 missing") fix_object=false ;;
    *) exit 3 ;;
esac
dirty=false
status=$(git status --porcelain)
if [[ -n "$status" ]]; then dirty=true; fi
remotes=false
remote_names=$(git remote)
remote_refs=$(git for-each-ref --format='%(refname)' refs/remotes)
if [[ -n "$remote_names$remote_refs" ]]; then remotes=true; fi
tags=false
tag_names=$(git tag --list)
if [[ -n "$tag_names" ]]; then tags=true; fi
reflog=$(git reflog --all --format='%H %gs')
fix_reflog=false
if grep -Fiq "$2" <<<"$reflog"; then fix_reflog=true; fi
evaluation_paths=""
for directory in /benchmark /inputs /results; do
    if [[ -d "$directory" ]]; then
        first=$(find "$directory"/ -mindepth 1 -maxdepth 1 -print -quit)
        if [[ -n "$first" ]]; then evaluation_paths="$evaluation_paths $directory"; fi
    elif [[ -e "$directory" || -L "$directory" ]]; then
        evaluation_paths="$evaluation_paths $directory"
    fi
done
patch_file=$(find /testbed -path /testbed/.git -prune -o -type f \
    \( -iname 'gold.patch' -o -iname 'gold_patch.diff' -o -iname 'test.patch' \
       -o -iname 'test_patch.diff' -o -iname 'model_patch.diff' -o -iname 'expected_tests.json' \) \
    -print -quit)
patch_artifact=false
if [[ -n "$patch_file" ]]; then patch_artifact=true; fi
printf 'head=%s\ntree=%s\ncommit_count=%s\nshallow=%s\nfix_object=%s\n' \
    "$head" "$tree" "$commit_count" "$shallow" "$fix_object"
printf 'dirty=%s\nremotes=%s\ntags=%s\nfix_reflog=%s\nevaluation_paths=%s\npatch_artifact=%s\n' \
    "$dirty" "$remotes" "$tags" "$fix_reflog" "$evaluation_paths" "$patch_artifact"
"""


def load_case(task_repo, instance_id):
    tasks = load_index(task_repo / "tasks/index.json")
    evaluation = task_repo / "evaluation"
    cases = load_index(evaluation / "index.json")
    task = tasks[instance_id]
    case = cases[instance_id]
    if any(task[key] != case[key] for key in ("case", "base_commit", "image")):
        raise ValueError("Task and evaluation indexes disagree on case, Base or image")
    config_path = f"cases/{case['case']}/evaluator/case_config.json"
    configs = [record for record in case["files"] if record["path"] == config_path]
    if len(configs) != 1:
        raise ValueError("Expected exactly one indexed case configuration")
    config = read_json(checked_file(evaluation, configs[0]))
    base, fix = task["base_commit"], config["fix_commit"]
    if not COMMIT.fullmatch(base) or not COMMIT.fullmatch(fix) or base == fix:
        raise ValueError("Invalid Base or Fix SHA")
    if config["base_commit"] != base:
        raise ValueError("Case configuration disagrees with the indexed Base")
    return task["image"], base, fix


def docker_output(docker, stage, *args, timeout=120):
    try:
        result = subprocess.run(
            [docker, *args], capture_output=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Docker {stage} timed out") from None
    if result.returncode:
        raise RuntimeError(f"Docker {stage} failed with exit code {result.returncode}")
    return result.stdout


def inspect_image(docker, image, override, pull):
    expected = image["image_id"]
    reference = image["pull_reference"]
    if not IMAGE_ID.fullmatch(expected):
        raise ValueError("Invalid indexed image ID")
    target = override or expected
    if pull:
        if not reference or reference.startswith("-") or not PINNED_REFERENCE.fullmatch(reference):
            raise ValueError("Pull requires a digest-pinned registry reference")
        docker_output(docker, "pull", "pull", reference, timeout=1800)
        target = reference
    info, = json.loads(docker_output(docker, "image inspection", "image", "inspect", "--", target))
    if not IMAGE_ID.fullmatch(info["Id"]) or (not override and info["Id"] != expected):
        raise ValueError("Local image does not match the selected identity")
    return info


def probe_container(docker, image_id, fix):
    name = f"clb-image-audit-{uuid4().hex}"
    try:
        output = docker_output(
            docker, "container probe", "run", "--rm", "--name", name, "--network", "none",
            "--pull=never", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--entrypoint", "/bin/bash", image_id, "-c", PROBE, "clb-image-audit", fix, fix[:7],
        )
    except (OSError, RuntimeError):
        try:
            subprocess.run([docker, "rm", "-f", name], capture_output=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            pass
        raise
    raw = dict(line.split("=", 1) for line in output.splitlines())
    checks = {"head": raw["head"], "tree": raw["tree"], "reachable_commits": int(raw["commit_count"]),
              "evaluation_paths": raw["evaluation_paths"].split()}
    for key in ("shallow", "fix_object", "dirty", "remotes", "tags", "fix_reflog", "patch_artifact"):
        if raw[key] not in ("true", "false"):
            raise ValueError(f"Invalid container probe value for {key}")
        checks[key] = raw[key] == "true"
    if not COMMIT.fullmatch(checks["head"]) or not COMMIT.fullmatch(checks["tree"]):
        raise ValueError("Container probe did not return valid Git identifiers")
    return checks


def fix_in_metadata(text, fix):
    tokens = re.findall(rf"(?<![0-9a-f]){fix[:7]}[0-9a-f]*", text.lower())
    return any(fix.startswith(token) for token in tokens)


def audit(args):
    image, base, fix = load_case(args.task_repo.resolve(), args.instance_id)
    info = inspect_image(args.docker, image, args.image, args.pull)
    checks = probe_container(args.docker, info["Id"], fix)
    history = docker_output(
        args.docker, "image history", "history", "--no-trunc", "--format", "{{json .CreatedBy}}",
        info["Id"],
    )
    metadata = {
        "image_config": fix_in_metadata(json.dumps(info["Config"]), fix),
        "image_history": fix_in_metadata(history, fix),
    }
    findings = [
        name for name, present in (
            ("base_mismatch", checks["head"] != base),
            ("unexpected_git_history", checks["reachable_commits"] != 1),
            ("fix_git_object", checks["fix_object"]),
            ("fix_in_git_reflog", checks["fix_reflog"]),
            ("git_remote_present", checks["remotes"]),
            ("git_tag_present", checks["tags"]),
            ("dirty_worktree", checks["dirty"]),
            ("nonempty_evaluation_paths", checks["evaluation_paths"]),
            ("suspected_patch_or_grading_file", checks["patch_artifact"]),
            ("fix_in_image_config", metadata["image_config"]),
            ("fix_in_image_history", metadata["image_history"]),
        ) if present
    ]
    return {"instance_id": args.instance_id, "status": "findings" if findings else "passed",
            "image_id": info["Id"], "expected_base": base, "container": checks,
            "metadata": metadata, "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    parser.add_argument("--task-repo", type=Path, required=True)
    parser.add_argument("--docker", default="docker")
    image = parser.add_mutually_exclusive_group()
    image.add_argument("--pull", action="store_true", help="Pull the indexed registry digest")
    image.add_argument("--image", help="Audit a locally built image in place of the indexed image")
    args = parser.parse_args()
    try:
        report = audit(args)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        report = {"instance_id": args.instance_id, "status": "error", "error": str(error)}
    print(json.dumps(report, indent=2))
    return {"passed": 0, "findings": 1, "error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
