"""Dispatch CLB SWE-bench commands."""

import argparse
from pathlib import Path
import subprocess
import sys

from .harness import runtime


PROJECT_ROOT = Path(runtime.__file__).resolve().parents[1]
RUNNERS = {"infer": "agent/run.py", "eval": "evaluation/evaluate.py"}


def check_dataset():
    tasks_root = PROJECT_ROOT / "tasks"
    evaluation_root = PROJECT_ROOT / "evaluation"
    tasks = runtime.load_index(tasks_root / "index.json")
    evaluators = runtime.load_index(evaluation_root / "index.json")
    if tasks.keys() != evaluators.keys():
        raise ValueError("Task and evaluation indexes contain different instance IDs")
    for instance_id, task in tasks.items():
        evaluation = evaluators[instance_id]
        for field in ("case", "cohort", "base_commit", "image"):
            if task[field] != evaluation[field]:
                raise ValueError(f"{instance_id}: indexes disagree on {field}")
        statement = runtime.read_json(runtime.checked_file(tasks_root, task["task"]))
        if statement["instance_id"] != instance_id or statement["base_commit"] != task["base_commit"]:
            raise ValueError(f"{instance_id}: statement identity or Base differs from the task index")
        for record in evaluation["files"]:
            runtime.checked_file(evaluation_root, record)
        runtime.checked_file(evaluation_root, evaluation["entrypoint"])
    print(f"Verified task records and evaluation assets for {len(tasks)} tasks")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog="clb", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("infer", help="Generate a patch with mini-SWE-agent")
    commands.add_parser("eval", help="Grade a candidate or a batch of predictions")
    dataset = commands.add_parser("dataset", help="Validate the task and evaluation datasets")
    dataset.add_subparsers(dest="action", required=True).add_parser(
        "check", help="Check task identities, asset paths, and SHA-256 hashes"
    )
    if not argv:
        parser.print_help()
        return 0
    command = argv[0]
    try:
        if command in RUNNERS:
            script = PROJECT_ROOT / RUNNERS[command]
            return subprocess.run([sys.executable, str(script), *argv[1:]]).returncode
        parser.parse_args(argv)
        check_dataset()
        return 0
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"{error}\n")
