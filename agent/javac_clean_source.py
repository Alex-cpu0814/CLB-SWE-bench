"""Disposable-container Base isolation. Compatible with Python 2.7 and 3.x."""
from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import hashlib


def git(root, *arguments):
    return subprocess.check_output(["git"] + list(arguments), cwd=root,
        stderr=subprocess.PIPE, universal_newlines=True).strip()


def child(path, root):
    actual = os.path.realpath(path)
    parent = os.path.realpath(root)
    if actual == parent or not actual.startswith(parent + os.sep):
        raise RuntimeError("Path outside disposable workspace: " + path)


def pack_base(root, clone, head):
    if git(root, "rev-list", "--count", head) != "1":
        raise RuntimeError("Expected one reachable Base commit")
    os.mkdir(clone)
    git(clone, "init", "-q")
    objects = subprocess.check_output(["git", "rev-list", "--objects", head], cwd=root).splitlines()
    object_ids = b"\n".join(line.split(b" ", 1)[0] for line in objects) + b"\n"
    metadata = os.path.join(clone, ".git")
    pack = subprocess.Popen(["git", "pack-objects", os.path.join(metadata, "objects", "pack", "pack")],
        cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, error = pack.communicate(object_ids)
    if pack.returncode:
        raise RuntimeError("Cannot pack the local Base objects: " + error.decode("utf-8", "replace"))
    with open(os.path.join(metadata, "shallow"), "w") as stream:
        stream.write(head + "\n")
    git(clone, "update-ref", "--no-deref", "HEAD", head)


def shallow(root):
    head, tree = git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")
    checkout_settings = {}
    for key in ("core.filemode", "core.symlinks", "core.ignorecase"):
        try:
            checkout_settings[key] = git(root, "config", "--get", key)
        except subprocess.CalledProcessError:
            pass
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("Tracked source is dirty")
    exclude = os.path.join(git(root, "rev-parse", "--git-dir"), "info", "exclude")
    if not os.path.isabs(exclude):
        exclude = os.path.join(root, exclude)
    contents = open(exclude, "rb").read() if os.path.isfile(exclude) else b""
    temporary = tempfile.mkdtemp(prefix=".formal-git-", dir=root)
    try:
        clone = os.path.join(temporary, "clone")
        try:
            subprocess.check_output(["git", "clone", "--no-local", "--no-checkout", "--depth=1",
                "file://" + root, clone], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            if b"attempt to fetch/clone from a shallow repository" not in error.output:
                raise
            clone = os.path.join(temporary, "packed")
            pack_base(root, clone, head)
        else:
            git(clone, "remote", "remove", "origin")
        if git(clone, "rev-parse", "HEAD") != head:
            raise RuntimeError("Base commit changed")
        for tag in git(clone, "tag", "--list").splitlines():
            git(clone, "tag", "--delete", tag)
        git(clone, "config", "core.autocrlf", "false")
        for key, value in checkout_settings.items():
            git(clone, "config", key, value)
        metadata = os.path.join(root, ".git")
        child(metadata, root)
        if os.path.islink(metadata) or os.path.isfile(metadata):
            os.unlink(metadata)
        elif os.path.isdir(metadata):
            shutil.rmtree(metadata)
        else:
            raise RuntimeError("Missing metadata")
        shutil.move(os.path.join(clone, ".git"), metadata)
        with open(os.path.join(metadata, "info/exclude"), "wb") as stream:
            stream.write(contents)
        git(root, "reset", "--mixed", "HEAD")
        if git(root, "rev-parse", "HEAD^{tree}") != tree or git(root, "rev-list", "--count", "HEAD") != "1":
            raise RuntimeError("Shallow identity check failed")
        if git(root, "remote") or git(root, "status", "--porcelain", "--untracked-files=no"):
            raise RuntimeError("Unexpected source or remote: " + git(root, "status", "--porcelain", "--untracked-files=no"))
        return {"head": head, "tree": tree, "reachable_commits": 1}
    finally:
        child(temporary, root)
        shutil.rmtree(temporary)


def isolate_075_cache():
    """Keep only verified external dependencies, not pre-generated source/tests."""
    root = "/benchmark"
    if set(os.listdir(root)) - set(("dependencies", "generated", "upstream_tests.json")):
        raise RuntimeError("Unexpected case075 benchmark assets")
    dependencies = os.path.join(root, "dependencies")
    child(dependencies, root)
    manifest = json.load(open(os.path.join(dependencies, "manifest.json")))
    if set(os.listdir(dependencies)) - set([item["file"] for item in manifest] + ["manifest.json", "kotlinc"]):
        raise RuntimeError("Unexpected dependency-cache entry")
    for item in manifest:
        filename = os.path.join(dependencies, item["file"])
        child(filename, dependencies)
        digest = hashlib.sha256()
        with open(filename, "rb") as stream:
            for data in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(data)
        if digest.hexdigest() != item["sha256"]:
            raise RuntimeError("Dependency hash mismatch")
    target = "/opt/base-dependencies"
    if os.path.exists(target):
        raise RuntimeError("Dependency destination already exists")
    shutil.move(dependencies, target)
    for name in ("generated", "upstream_tests.json"):
        entry = os.path.join(root, name)
        if not os.path.exists(entry):
            continue
        child(entry, root)
        if os.path.isdir(entry):
            shutil.rmtree(entry)
        else:
            os.unlink(entry)
    return {"verified_dependency_files": [item["file"] for item in manifest],
        "dependency_location": target, "pre_generated_source_and_scoring_list_removed": True}


def prepare(expected, case):
    root = "/testbed"
    if git(root, "rev-parse", "HEAD") != expected:
        raise RuntimeError("Wrong Base in image")
    cache = None
    if case == "javac_case_075" and os.path.isdir("/benchmark/dependencies"):
        cache = isolate_075_cache()
    for private in ("/benchmark", "/inputs", "/results"):
        if os.path.exists(private) and (not os.path.isdir(private) or os.listdir(private)):
            raise RuntimeError("Unexpected private evaluation assets: " + private)
    if git(root, "status", "--porcelain"):
        raise RuntimeError("Initial checkout is not clean")
    modules = []
    for line in git(root, "submodule", "status", "--recursive").splitlines():
        if not line or line.startswith("-"):
            continue
        if line[0] in "+U":
            raise RuntimeError("Submodule does not match Base")
        module = os.path.join(root, line.strip().split()[1])
        child(module, root)
        modules.append(module)
    audit = {"submodules": {}}
    for module in sorted(modules, key=lambda item: item.count("/"), reverse=True):
        audit["submodules"][os.path.relpath(module, root)] = shallow(module)
    audit["main"] = shallow(root)
    if git(root, "status", "--porcelain"):
        raise RuntimeError("Checkout changed after isolation")
    audit["private_asset_directories_empty"] = True
    if cache:
        audit["isolated_dependency_cache"] = cache
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("--case", required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.base, arguments.case), sort_keys=True))
