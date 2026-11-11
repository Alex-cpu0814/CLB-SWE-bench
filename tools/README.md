# Audit a CLB Base image

Run [`audit_image.py`](audit_image.py) from the `CLB-SWE-bench` checkout. Use Docker in Linux container mode and a matching `CLB-SWE-bench-tasks` checkout with the task and evaluation indexes. The image must have Bash and Git, with the Base repository at `/testbed`.

## Check a local build before publishing

Pass the task's instance ID and the candidate image's local tag or image ID.

```bash
python tools/audit_image.py clb-pyc-034 --task-repo ../CLB-SWE-bench-tasks --image clb-local/pyc-case-034:batch-v2
```

## Check a published image

Use `--pull` to pull the registry reference pinned by digest in the task index.

```bash
python tools/audit_image.py clb-pyc-034 --task-repo ../CLB-SWE-bench-tasks --pull
```

With neither `--image` nor `--pull`, the script uses the image ID from the index and expects that image to be available locally.

## Read the report

The script checks the Git checkout in a temporary container with networking disabled. It compares `HEAD` with the indexed Base and checks reachable commits, the Fix object and reflog, tags, remotes, worktree status, and common evaluation artifacts. It also searches the image configuration and the full `CreatedBy` fields from `docker history` for the known Fix SHA or an abbreviation of at least seven characters.

| Exit code | JSON status | Meaning |
| --- | --- | --- |
| `0` | `passed` | The checks completed without findings. |
| `1` | `findings` | Review the entries in `findings` before publishing. |
| `2` | `error` | The audit could not complete. Review the error and rerun it. |
