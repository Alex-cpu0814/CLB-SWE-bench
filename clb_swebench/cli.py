"""Dispatch CLB SWE-bench commands."""

import argparse
from pathlib import Path
import subprocess
import sys

from .harness import evaluate, runtime


PROJECT_ROOT = Path(runtime.__file__).resolve().parents[1]


def check_dataset(task_repo):
    tasks_root = (task_repo / "tasks").resolve()
    evaluation_root = (task_repo / "evaluation").resolve()
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
    check = dataset.add_subparsers(dest="action", required=True).add_parser(
        "check", help="Check task identities, asset paths, and SHA-256 hashes"
    )
    check.add_argument("task_repo", type=Path, help="Path to a CLB task repository")
    if not argv:
        parser.print_help()
        return 0
    command = argv[0]
    try:
        if command == "infer":
            script = PROJECT_ROOT / "agent/run.py"
            return subprocess.run([sys.executable, str(script), *argv[1:]]).returncode
        if command == "eval":
            return evaluate.main(argv[1:])
        args = parser.parse_args(argv)
        check_dataset(args.task_repo)
        return 0
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"{error}\n")
