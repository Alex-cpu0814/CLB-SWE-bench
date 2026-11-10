# Evaluation

Run from the project root. Run the evaluator after candidate generation is complete. Python 3.10+ and Docker with Linux containers are required. The evaluation runner uses the Python standard library.

~~~bash
clb dataset check
clb eval run clb-javac-068 --pull \
  --patch handoff/model_patch.diff --output-root grading --run-id lwjgl-first
~~~

Use a new `--run-id` for every evaluation. `summary.json` records the F2P and P2P counts in the selected output directory. The shared evaluator creates isolated containers and mount the candidate, test patch and case-specific runtime assets. In the source tree, each case stores its grading list at `grading/expected_tests.json`. It contains `instance_id`, `FAIL_TO_PASS` and `PASS_TO_PASS`.

The evaluator uses the selected native Docker CLI. The historical Windows Java batch also used a resource-limiting Docker launcher for evaluation. Compare host resource settings when attempting exact performance or timeout replication.

See [index.json](index.json) for task IDs, asset hashes and immutable image references. `javac_case_069` and `javac_case_075` use the published Base images. Both replays matched the original F2P and P2P results.

The case evaluators use the shared logging implementation in [harness/logging_v3.py](../harness/logging_v3.py).

The Python–C evaluators mount [the shared container runner](shared/run_python_c.sh). Each case supplies its own `case_adapter.sh` with build and test commands.

The case entry points select a test-log parser and execution profile. [The shared evaluator](../harness/case_evaluator.py) handles Docker, candidate evaluation, and report generation.
