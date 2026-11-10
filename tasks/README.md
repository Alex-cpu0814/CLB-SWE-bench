# Public task package

[index.json](index.json) maps `instance_id` to the public statement, Base commit and image identity for each task. The per-task JSON preserves the frozen `problem_statement` text and task identity. The launcher sends the statement through the pinned mini-SWE-agent template.

Run from the project root. In a Python 3.12 virtual environment, install the pinned dependencies using `python -m pip install -r agent/requirements-lock.txt`.

~~~bash
python agent/run.py clb-javac-068 --pull --preflight --output-dir runs/lwjgl-preflight
python agent/run.py clb-javac-068 --output-dir runs/lwjgl-generation
~~~

The second command uses a paid model endpoint. Provide the key at the local prompt or through the `CLB_MODEL_API_KEY` environment variable. Each run requires a fresh output directory. Send only the submitted candidate diff and its `instance_id` to the evaluator operator.

All 72 records have pinned registry references. Java 069 and Java 075 use the published Base images. The `historical_image_id` for these cases records the image used in the original experiment. The launchers compare the locally loaded image ID with the delivery index.

Use the exact CLB ID in the index. Python–C IDs follow `clb-pyc-<number>` and Java–C IDs follow `clb-javac-<number>`.
