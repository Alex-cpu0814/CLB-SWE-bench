"""Derive CLB Base commits from the Fix links in the editable selection workbook."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
SHEET = "analysis result"
SOURCE_DIR = ROOT / "data/sources/artifact-B457/Manual_Bug_Analysis_Result"
SELECTION = ROOT / "data/selection"
SHA = re.compile(r"[a-f0-9]{40}", re.IGNORECASE)
LINK = re.compile(r"https://github\.com/([\w.-]+/[\w.-]+)/commit/([a-f0-9]{40})/?", re.IGNORECASE)
REQUIRED_HEADERS = (
    "Case", "Link", "Instance ID", "Cohort", "Source Workbook", "Source Case", "Source Excel Row",
)


def read_sheet(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return list(book[SHEET].values)
    finally:
        book.close()


def commit_key(url):
    match = LINK.fullmatch(str(url).strip())
    if not match:
        raise ValueError(f"expected a GitHub commit URL with a full Fix SHA: {url}")
    return match[1], match[2].lower()


def load_selection(path, source_dir):
    headers, *rows = read_sheet(path)
    columns = {}
    for name in REQUIRED_HEADERS:
        if headers.count(name) != 1:
            raise ValueError(f"Expected one column named {name!r} in {path}")
        columns[name] = headers.index(name)
    sources = {}
    selected = {}
    for row_number, row in enumerate(rows, 2):
        fields = {name: row[index] for name, index in columns.items()}
        present = [value is not None and bool(str(value).strip()) for value in fields.values()]
        if not any(present):
            continue
        if not all(present):
            raise ValueError(f"Selection row {row_number} has missing required fields")
        try:
            repo, fix = commit_key(fields["Link"])
            instance_id = str(fields["Instance ID"]).strip()
            if instance_id in selected:
                raise ValueError(f"duplicate Instance ID {instance_id!r}")
            filename = str(fields["Source Workbook"]).strip()
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.xlsx", filename):
                raise ValueError(f"invalid source workbook filename {filename!r}")
            if filename not in sources:
                sources[filename] = read_sheet(source_dir / filename)
                if sources[filename][0][:2] != ("Case", "Link"):
                    raise ValueError(f"expected Case and Link in the first two columns of {filename}")
            source_row = int(fields["Source Excel Row"])
            if source_row != float(fields["Source Excel Row"]) or not 2 <= source_row <= len(sources[filename]):
                raise ValueError(f"invalid source Excel row {fields['Source Excel Row']!r}")
            source_case, source_link = sources[filename][source_row - 1][:2]
            original_repo, original_fix = commit_key(source_link)
            if (str(source_case).strip() != str(fields["Source Case"]).strip()
                    or (original_repo.casefold(), original_fix) != (repo.casefold(), fix)):
                raise ValueError(f"Case or Fix link does not match {filename} row {source_row}")
        except (ValueError, KeyError, OSError, TypeError) as error:
            raise ValueError(f"Selection row {row_number}: {error}") from error
        selected[instance_id] = {
            "case": str(fields["Case"]).strip(), "instance_id": instance_id,
            "cohort": str(fields["Cohort"]).strip(), "repo": repo, "fix_commit": fix,
            "source_workbook": filename, "source_sheet": SHEET,
            "source_case": str(source_case), "source_excel_row": source_row,
        }
    if not selected:
        raise ValueError("The selection workbook has no case rows")
    return selected


def load_parent_records(path):
    source = json.loads(path.read_text(encoding="utf-8-sig"))
    if source["schema_version"] != 1:
        raise ValueError(f"Unsupported parent record schema: {path}")
    records = {}
    for record in source["commits"]:
        key = record["repo"].casefold(), record["fix_commit"].lower()
        if key in records or not SHA.fullmatch(key[1]):
            raise ValueError(f"Invalid or duplicate parent record: {key}")
        records[key] = record
    return records


def fetch_parents(repo, fix):
    url = f"https://api.github.com/repos/{repo}/git/commits/{fix}"
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "CLB-SWE-bench"})
    try:
        with urlopen(request, timeout=20) as response:
            commit = json.load(response)
    except HTTPError as error:
        raise ValueError(f"GitHub HTTP {error.code} for {repo} {fix}") from error
    except URLError as error:
        raise ValueError(f"Could not query GitHub for {repo} {fix}: {error.reason}") from error
    if commit.get("sha") != fix:
        raise ValueError(f"GitHub returned a different commit for {repo} {fix}")
    return {"parents": [parent["sha"] for parent in commit["parents"]], "evidence": url}


def resolve_bases(selected, records, allow_github):
    results = {}
    for instance, case in selected.items():
        repo, fix = case["repo"], case["fix_commit"]
        key = repo.casefold(), fix
        if key not in records:
            if not allow_github:
                raise ValueError(f"{instance}: no parent record for {fix}. Use --github to query the public API.")
            records[key] = fetch_parents(repo, fix)
        record = records[key]
        parents = record["parents"]
        if (not isinstance(parents, list) or len(parents) not in (1, 2)
                or not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in parents)
                or len(set(parents)) != len(parents) or fix in parents):
            raise ValueError(f"{instance}: invalid parents or unsupported parent count; review Base manually")
        results[instance] = {
            **case, "base_commit": parents[0], "parents": parents,
            "selection_rule": "single_parent" if len(parents) == 1 else "merge_first_parent",
            "needs_merge_review": len(parents) == 2, "parent_evidence": record["evidence"],
        }
    return results


def verify_manifest(results, path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    frozen = {case["instance_id"]: case for case in data["cases"]}
    if frozen.keys() != results.keys():
        missing = sorted(frozen.keys() - results.keys())
        extra = sorted(results.keys() - frozen.keys())
        raise ValueError(f"Selection differs from frozen manifest; missing={missing}, extra={extra}")
    for instance, result in results.items():
        expected = frozen[instance]
        config_path = path.parent.parent / expected["evaluation"]["config"]["path"]
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        identity = result["case"], result["cohort"], result["repo"].casefold(), result["fix_commit"], result["base_commit"]
        frozen_identity = (expected["case"], expected["cohort"], expected["repository"].casefold(),
                           config["fix_commit"], expected["base_commit"])
        if identity != frozen_identity:
            raise ValueError(f"{instance}: case, Fix or derived Base differs from the frozen manifest")


def verify_task_index(results, path):
    task_root = path.resolve().parent
    index = json.loads(path.read_text(encoding="utf-8-sig"))
    released = {task["instance_id"]: task for task in index["cases"]}
    if len(released) != index["record_count"] or released.keys() != results.keys():
        raise ValueError("Selection and release task index contain different instances")
    for instance, result in results.items():
        record = released[instance]
        task_ref = record["task"]
        task_path = (task_root / task_ref["path"]).resolve()
        if not task_path.is_relative_to(task_root):
            raise ValueError(f"{instance}: task path leaves the release task directory")
        payload = task_path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != task_ref["sha256"]:
            raise ValueError(f"{instance}: released task SHA-256 does not match the index")
        task = json.loads(payload)
        if (result["case"] != record["case"] or result["cohort"] != record["cohort"]
                or task["instance_id"] != instance or result["repo"].casefold() != task["repo"].casefold()
                or result["base_commit"] != record["base_commit"] or result["base_commit"] != task["base_commit"]):
            raise ValueError(f"{instance}: case identity or derived Base differs from the release task")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, default=SELECTION / "v1.2" / "clb_cases.xlsx")
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--parents", type=Path, default=SELECTION / "fix-parents.json")
    parser.add_argument("--github", action="store_true", help="Query GitHub for missing parent records")
    verify = parser.add_mutually_exclusive_group()
    verify.add_argument("--verify-manifest", type=Path, help="Compare against the maintainer workspace manifest")
    verify.add_argument("--verify-task-index", type=Path, help="Compare against the release task index and public tasks")
    args = parser.parse_args()
    try:
        cases = load_selection(args.selection, args.source_dir)
        results = resolve_bases(cases, load_parent_records(args.parents), args.github)
        if args.verify_manifest:
            verify_manifest(results, args.verify_manifest)
        if args.verify_task_index:
            verify_task_index(results, args.verify_task_index)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    for result in results.values():
        print(json.dumps(result, ensure_ascii=False))
    merges = sum(result["needs_merge_review"] for result in results.values())
    print(f"{len(results)} cases: {len(results) - merges} single-parent, {merges} two-parent", file=sys.stderr)


if __name__ == "__main__":
    main()
