"""Check or grade candidates with the packaged per-case CLB evaluators."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

from .runtime import checked_file, ensure_image, load_index, write_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_RUNNER = "shared/run_python_c.sh"
EVALUATION_ERRORS = (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError)


def valid_run_id(value):
    return (isinstance(value, str) and value not in {".", ".."}
            and re.fullmatch(r"[A-Za-z0-9_.-]+", value) is not None)


def add_run_options(parser):
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--timeout", type=int, default=1800)


def run_candidate(case, patch, output_root, run_id, *, evaluation_root, docker, pull, timeout):
    assets = {record["path"]: checked_file(evaluation_root, record) for record in case["files"]}
    evaluator = checked_file(evaluation_root, case["entrypoint"])
    image_id = ensure_image(docker, case["image"], pull)
    child_env = {key: value for key, value in os.environ.items()
                 if not key.upper().endswith(("API_KEY", "TOKEN", "SECRET"))}
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Case scripts use the top-level harness import in source and installed layouts.
    python_paths = [str(PROJECT_ROOT)]
    if child_env.get("PYTHONPATH"):
        python_paths.append(child_env["PYTHONPATH"])
    child_env["PYTHONPATH"] = os.pathsep.join(python_paths)
    command = [sys.executable, str(evaluator), "--docker", docker, "--image", image_id,
               "--patch", str(patch.resolve()), "--output-root", str(output_root.resolve()),
               "--run-id", run_id, "--timeout", str(timeout)]
    if SHARED_RUNNER in assets:
        command.extend(("--shared-runner", str(assets[SHARED_RUNNER])))
    return subprocess.run(command, env=child_env).returncode


def read_predictions(path, cases):
    predictions = {}
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid prediction JSON on line {number}: {error.msg}") from error
            if not isinstance(record, dict) or "model_patch" not in record:
                raise ValueError(f"Prediction on line {number} must have instance_id and model_patch")
            instance = record.get("instance_id")
            if not valid_run_id(instance) or instance not in cases:
                raise ValueError(f"Unknown or invalid instance_id on line {number}: {instance!r}")
            if instance in predictions:
                raise ValueError(f"Duplicate prediction for {instance} on line {number}")
            patch = record["model_patch"]
            if patch is not None and not isinstance(patch, str):
                raise ValueError(f"model_patch on line {number} must be a string or null")
            predictions[instance] = patch.encode("utf-8") if patch and patch.strip() else None
    if not predictions:
        raise ValueError("Predictions file must contain at least one record")
    return predictions


def run_batch(predictions, cases, output_root, run_id, **options):
    directory = output_root / run_id
    directory.mkdir(parents=True, exist_ok=False)
    counts = dict.fromkeys(("resolved", "unresolved", "no_submission", "error"), 0)
    report = {"run_id": run_id, "prediction_count": len(predictions),
              "pending": len(predictions), "counts": counts, "cases": []}
    summary_path = directory / "summary.json"
    write_json(summary_path, report)
    with TemporaryDirectory(prefix=".patches-", dir=directory) as temporary:
        for instance, patch in predictions.items():
            result = {"instance_id": instance, "case": cases[instance]["case"], "exit_code": None}
            if patch is None:
                result["status"] = "no_submission"
            else:
                try:
                    patch_path = Path(temporary) / f"{instance}.diff"
                    patch_path.write_bytes(patch)
                    code = run_candidate(cases[instance], patch_path, directory / "cases", instance, **options)
                    result["exit_code"] = code
                    case_summary = Path("cases") / instance / "summary.json"
                    if (directory / case_summary).is_file():
                        result["summary"] = case_summary.as_posix()
                    elif code in (0, 1):
                        raise RuntimeError("Evaluator did not write summary.json")
                    result["status"] = {0: "resolved", 1: "unresolved"}.get(code, "error")
                except EVALUATION_ERRORS as error:
                    result.update(status="error", error=str(error))
            counts[result["status"]] += 1
            report["cases"].append(result)
            report["pending"] -= 1
            write_json(summary_path, report)
            print(f"{instance}: {result['status']}", flush=True)
    print(f"Batch summary: {summary_path}")
    return 2 if counts["error"] else int(bool(counts["unresolved"] or counts["no_submission"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Check all evaluator assets against the release index")
    run = commands.add_parser("run", help="Grade one candidate in a fresh container")
    run.add_argument("instance_id")
    run.add_argument("--patch", type=Path, required=True)
    add_run_options(run)
    batch = commands.add_parser("batch", help="Grade a JSONL file of candidate patches")
    batch.add_argument("--predictions", type=Path, required=True)
    add_run_options(batch)
    for command in (check, run, batch):
        command.add_argument("--task-repo", type=Path, required=True,
                             help="Path to a CLB task repository")
    args = parser.parse_args(argv)
    try:
        evaluation_root = (args.task_repo / "evaluation").resolve()
        cases = load_index(evaluation_root / "index.json")
        if args.command == "check":
            for case in cases.values():
                for record in case["files"]:
                    checked_file(evaluation_root, record)
            print(f"Verified evaluator assets for {len(cases)} tasks")
            return 0
        if not valid_run_id(args.run_id):
            raise ValueError("Provide a valid run ID")
        if (args.output_root / args.run_id).exists() or args.timeout <= 0:
            raise ValueError("Use a new run ID and a positive timeout")
        options = {"evaluation_root": evaluation_root, "docker": args.docker,
                   "pull": args.pull, "timeout": args.timeout}
        if args.command == "batch":
            predictions = read_predictions(args.predictions, cases)
            return run_batch(predictions, cases, args.output_root, args.run_id, **options)
        case = cases[args.instance_id]
        if not args.patch.is_file():
            raise ValueError("Provide an existing patch")
        return run_candidate(case, args.patch, args.output_root, args.run_id, **options)
    except EVALUATION_ERRORS as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
