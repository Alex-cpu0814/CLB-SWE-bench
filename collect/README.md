# Reproduce the CLB selection

The selection workbook records the CLB case and instance IDs, Fix links, and source rows. The parent snapshot records the ordered parents of the selected fixes. [Selection workbook](../data/selection/v1.2/clb_cases.xlsx) · [Fix parent snapshot](../data/selection/fix-parents.json)

## Verify the Base commits

Download artifact_bugstudy.zip from the upstream artifact record and extract it. The --source-dir argument points to the extracted Manual_Bug_Analysis_Result directory containing pyc_case_study.xlsx and javac_case_study.xlsx. [Dissecting Real-World Cross-Language Bugs, artifact v4](https://zenodo.org/records/15204223)

From the repository root, run the following with the actual path to the extracted workbooks.

~~~bash
python -m pip install openpyxl==3.1.5
python collect/extract_base_commits.py --source-dir "/path/to/Manual_Bug_Analysis_Result" --verify-task-index tasks/index.json
~~~

The verifier checks the workbook rows against the source and derives each Base from the first parent of the Fix. It compares the result with the 72 task records. For the released snapshot, 38 fixes have one parent and 34 have two parents.

## Extract upstream patches

The plans specify the upstream diff SHA-256, the files assigned to each patch, and any excluded files. Use the plan's upstream_diff_url for a text diff. For a binary diff, use the upstream repository and Git arguments in upstream_diff_source.

~~~bash
python collect/extract_upstream_patches.py --plan data/selection/patch-plans/case002.json --diff /path/to/upstream.diff --output-dir /path/to/new-output
~~~

The extractor checks the diff and produces gold_patch.diff and test_patch.diff. There are 60 extraction plans. CLB-authored and adapted test patches are included with the corresponding evaluation cases. [Extraction plans](../data/selection/patch-plans/) · [Evaluation guide](../evaluation/README.md)
