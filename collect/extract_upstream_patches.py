"""Split a reviewed upstream diff into gold and test patches."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def split_diff(diff, plan):
    if hashlib.sha256(diff).hexdigest() != plan["upstream_diff_sha256"]:
        raise ValueError("Input SHA-256 does not match the reviewed upstream diff")

    groups = {
        "gold_patch.diff": plan["gold_files"],
        "test_patch.diff": plan["test_files"],
    }
    excluded = plan.get("excluded_files", {})
    if not isinstance(excluded, dict) or any(
        not path.strip() or not isinstance(reason, str) or not reason.strip()
        for path, reason in excluded.items()
    ):
        raise ValueError("Each excluded path must have a nonempty reason")

    expected = groups["gold_patch.diff"] + groups["test_patch.diff"] + list(excluded)
    if not all(groups.values()):
        raise ValueError("Gold and test paths must be nonempty")
    if len(set(expected)) != len(expected):
        raise ValueError("Gold, test and excluded paths must be unique and disjoint")

    headers = list(re.finditer(rb"(?m)^diff --git [^\n]+\n", diff))
    if not headers or headers[0].start() != 0:
        raise ValueError("Expected a Git diff starting with a file header")
    blocks = {}
    for header, end in zip(headers, [h.start() for h in headers[1:]] + [len(diff)]):
        paths = re.fullmatch(rb"diff --git a/(\S+) b/(\S+)\n", header.group())
        if not paths or paths[1] != paths[2]:
            raise ValueError(f"Unsupported diff header: {header.group()!r}")
        path = paths[1].decode("utf-8")
        if path in blocks:
            raise ValueError(f"Duplicate diff path: {path}")
        blocks[path] = diff[header.start():end]

    missing = set(expected) - blocks.keys()
    unclassified = blocks.keys() - set(expected)
    if missing or unclassified:
        raise ValueError(f"Missing paths: {sorted(missing)}; unclassified paths: {sorted(unclassified)}")

    return {
        name: b"".join(block for path, block in blocks.items() if path in paths)
        for name, paths in groups.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--diff", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, help="Write patches to a new directory")
    args = parser.parse_args()

    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        patches = split_diff(args.diff.read_bytes(), plan)
        if args.output_dir is not None:
            args.output_dir.mkdir()
            for name, patch in patches.items():
                (args.output_dir / name).write_bytes(patch)
    except (KeyError, OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")

    report = {
        "case_id": plan["case_id"],
        "gold_files": plan["gold_files"],
        "test_files": plan["test_files"],
        "patch_sha256": {
            name: hashlib.sha256(patch).hexdigest()
            for name, patch in patches.items()
        },
    }
    if plan.get("excluded_files"):
        report["excluded_files"] = plan["excluded_files"]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
