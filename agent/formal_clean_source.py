"""Disposable-container Base isolation. Compatible with Python 2.7 and 3.x."""
from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import tempfile


def git(root, *arguments):
    return subprocess.check_output(["git", "-C", root] + list(arguments),
        stderr=subprocess.STDOUT, universal_newlines=True).strip()


def child(path, root):
    actual = os.path.realpath(path)
    parent = os.path.realpath(root)
    if actual == parent or not actual.startswith(parent + os.sep):
        raise RuntimeError("Path outside disposable workspace: " + path)


def shallow(root):
    head, tree = git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")
    if git(root, "status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("Tracked source is dirty")
    exclude = git(root, "rev-parse", "--git-path", "info/exclude")
    if not os.path.isabs(exclude):
        exclude = os.path.join(root, exclude)
    contents = open(exclude, "rb").read() if os.path.isfile(exclude) else b""
    temporary = tempfile.mkdtemp(prefix=".formal-git-", dir=root)
    try:
        clone = os.path.join(temporary, "clone")
        subprocess.check_output(["git", "clone", "--no-local", "--no-checkout", "--depth=1",
            "--no-tags", "file://" + root, clone], stderr=subprocess.STDOUT)
        if git(clone, "rev-parse", "HEAD") != head:
            raise RuntimeError("Base commit changed")
        git(clone, "remote", "remove", "origin")
        git(clone, "config", "core.autocrlf", "false")
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
            raise RuntimeError("Unexpected source or remote")
        return {"head": head, "tree": tree, "reachable_commits": 1}
    finally:
        child(temporary, root)
        shutil.rmtree(temporary)


def prepare(expected):
    root = "/testbed"
    if git(root, "rev-parse", "HEAD") != expected:
        raise RuntimeError("Wrong Base in image")
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
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    print(json.dumps(prepare(parser.parse_args().base), sort_keys=True))
