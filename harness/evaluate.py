"""Check or grade candidates with the packaged per-case CLB evaluators."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

from .runtime import checked_file, ensure_image, load_index


EVALUATION_ROOT = Path(__file__).resolve().parents[1] / "evaluation"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Check all evaluator assets against the release index")
    run = commands.add_parser("run", help="Grade one candidate in a fresh container")
    run.add_argument("instance_id")
    run.add_argument("--patch", type=Path, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--docker", default="docker")
    run.add_argument("--pull", action="store_true")
    run.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    try:
        cases = load_index(EVALUATION_ROOT / "index.json")
        if args.command == "check":
            for case in cases.values():
                for record in case["files"]:
                    checked_file(EVALUATION_ROOT, record)
            print(f"Verified evaluator assets for {len(cases)} tasks")
            return 0
        case = cases[args.instance_id]
        for record in case["files"]:
            checked_file(EVALUATION_ROOT, record)
        evaluator = checked_file(EVALUATION_ROOT, case["entrypoint"])
        if not args.patch.is_file() or not re.fullmatch(r"[A-Za-z0-9_.-]+", args.run_id) or args.run_id in {".", ".."}:
            raise ValueError("Provide an existing patch and a valid run ID")
        if (args.output_root / args.run_id).exists() or args.timeout <= 0:
            raise ValueError("Use a new run ID and a positive timeout")
        image_id = ensure_image(args.docker, case["image"], args.pull)
        child_env = {key: value for key, value in os.environ.items()
                     if not key.upper().endswith(("API_KEY", "TOKEN", "SECRET"))}
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run([sys.executable, str(evaluator), "--docker", args.docker,
                               "--image", image_id, "--patch", str(args.patch.resolve()),
                               "--output-root", str(args.output_root.resolve()), "--run-id", args.run_id,
                               "--timeout", str(args.timeout)], env=child_env).returncode
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
