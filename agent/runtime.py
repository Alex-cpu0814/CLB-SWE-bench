import hashlib
import json
from pathlib import Path
import re
import subprocess


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def checked_file(root, record):
    path = (root / record["path"]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing or invalid package file: {record['path']}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {record['path']}")
    return path


def load_index(path):
    data = read_json(path)
    records = {case["instance_id"]: case for case in data["cases"]}
    if len(records) != len(data["cases"]) or len(records) != data["record_count"]:
        raise ValueError("Unexpected task count or duplicate instance ID")
    return records


def docker_output(docker, *args, timeout=60):
    result = subprocess.run([docker, *map(str, args)], capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def ensure_image(docker, image, pull):
    expected = image["image_id"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected):
        raise ValueError("Invalid image ID")
    reference = image["pull_reference"]

    def inspect():
        return subprocess.run([docker, "image", "inspect", "--format", "{{.Id}}", expected],
                              capture_output=True, encoding="utf-8", errors="replace", timeout=30)

    result = inspect()
    if result.returncode:
        if "no such image" not in result.stderr.lower():
            raise RuntimeError(result.stderr.strip() or "Docker image inspection failed")
        if not reference:
            raise RuntimeError(f"Local-only Base image {expected} is missing. See the release README.")
        if not pull:
            raise RuntimeError(f"Base image {expected} is missing. Use --pull for {reference}.")
        if not re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", reference):
            raise ValueError("Invalid immutable registry reference")
        docker_output(docker, "pull", reference, timeout=1800)
        result = inspect()
    if result.returncode or result.stdout.strip() != expected:
        raise RuntimeError(f"Local image does not match frozen ID {expected}")
    return expected
