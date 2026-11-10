# Evaluator package

Run from the project root. Run the evaluator after candidate generation is complete. Python 3.10+ and Docker with Linux containers are required. The evaluation runner uses the Python standard library.

~~~bash
python -m harness.evaluate check
python -m harness.evaluate run clb-javac-068 --pull \
  --patch handoff/model_patch.diff --output-root grading --run-id lwjgl-first
~~~

Use a new `--run-id` for every evaluation. `summary.json` records the F2P and P2P counts in the selected output directory. The original per-task evaluators create isolated containers and mount the candidate, test patch and case-specific runtime assets. In the source tree, each case stores its grading list at `grading/expected_tests.json`. It contains `instance_id`, `FAIL_TO_PASS` and `PASS_TO_PASS`.

The packaged evaluator launcher uses the selected native Docker CLI. The historical Windows Java batch also used a resource-limiting Docker launcher for evaluation. Compare host resource settings when attempting exact performance or timeout replication.

See [index.json](index.json) for task IDs, asset hashes and immutable image references. `javac_case_069` and `javac_case_075` use the published Base images. Both replays matched the original F2P and P2P results.
