# Reproduce the CLB selection

The companion task checkout contains `data/selection/v1.2/clb_cases.xlsx` with the CLB case and instance IDs, Fix links and source rows. Its `data/selection/fix-parents.json` records the ordered parents of the selected fixes.

## Verify the Base commits

Download and extract the upstream `artifact_bugstudy.zip`. Pass the directory that contains `pyc_case_study.xlsx` and `javac_case_study.xlsx` to `--source-dir`. [Dissecting Real-World Cross-Language Bugs, artifact v4](https://zenodo.org/records/15204223)

From the code repository root, substitute the paths to the extracted workbooks and task checkout.

```bash
python -m pip install openpyxl==3.1.5
python collect/extract_base_commits.py   --source-dir "/path/to/Manual_Bug_Analysis_Result"   --selection ../CLB-SWE-bench-tasks/data/selection/v1.2/clb_cases.xlsx   --parents ../CLB-SWE-bench-tasks/data/selection/fix-parents.json   --verify-task-index ../CLB-SWE-bench-tasks/tasks/index.json
```

The verifier checks the workbook rows against the source, derives each Base from the first parent of the Fix, and compares it with the 72 task records. The released snapshot has 38 single-parent fixes and 34 two-parent fixes.

## Extract upstream patches

The plans in the task checkout specify the upstream diff SHA-256, the files assigned to each patch, and any excluded files. Use the plan's `upstream_diff_url` for a text diff. For a binary diff, use the repository and Git arguments in `upstream_diff_source`.

```bash
python collect/extract_upstream_patches.py   --plan ../CLB-SWE-bench-tasks/data/selection/patch-plans/case002.json   --diff /path/to/upstream.diff --output-dir /path/to/new-output
```

The extractor checks the diff and writes `gold_patch.diff` and `test_patch.diff`. There are 60 extraction plans. The task checkout contains the released Test Patches, including the CLB-authored and adapted patches.
