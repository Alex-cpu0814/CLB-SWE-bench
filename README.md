# CLB SWE-bench

CLB SWE-bench evaluates software repair on 72 cross-language bugs. The test split includes 50 Python–C tasks, 11 Java–C tasks with upstream-derived tests, and 11 Java–C tasks with tests written by the CLB authors.

Each task starts from a pinned Docker image and a Base commit. Use the same CLB instance ID in the dataset, the generation runner, and the evaluator. [Hugging Face dataset](https://huggingface.co/datasets/Alex-cpu0814/CLB-SWE-bench) · [Pinned dataset revision](https://huggingface.co/datasets/Alex-cpu0814/CLB-SWE-bench/tree/4e278eb55c8e58ca202fd2ecd15fbee2f1af5484)

## Quickstart

From the repository root, use Python 3.12 in a virtual environment and Docker configured for Linux containers.

### Generate a candidate

~~~bash
python -m pip install -r agent/requirements-lock.txt
python agent/run.py clb-pyc-086 --pull --preflight --output-dir runs/case086-preflight
python agent/run.py clb-pyc-086 --pull --output-dir runs/case086-generation
~~~

The preflight verifies the Base without a model API call. Generation can incur model charges. Set the provider and model in the agent configuration and enter the API key at the local prompt or set the CLB_MODEL_API_KEY environment variable. A successful submission writes model_patch.diff in the output directory. Use a fresh output directory for each run. [Agent configuration](agent/config.json) · [Task guide](tasks/README.md)

### Evaluate the candidate

~~~bash
python -m harness.evaluate check
python -m harness.evaluate run clb-pyc-086 --pull --patch runs/case086-generation/model_patch.diff --output-root grading --run-id case086-first
~~~

Read grading/case086-first/summary.json for the result and test counts. The evaluator returns 0 for resolved, 1 for unresolved, and 2 for an error. [Evaluator guide](evaluation/README.md)

## Repository layout

| Directory | Contents |
| --- | --- |
| [agent/](agent/run.py) | mini-SWE-agent launcher and Base workspace preparation |
| [harness/](harness/evaluate.py) | Shared evaluation entry point and asset verification |
| [tasks/](tasks/index.json) | Runtime snapshot of the task records and pinned image references |
| [evaluation/](evaluation/index.json) | Case-specific evaluators, test patches, and scoring lists |
| [collect/](collect/README.md) | Case selection checks, Base derivation, and patch extraction |
| [data/selection/](data/selection/) | CLB selection workbook, parent records, and extraction plans |

The full dataset contains reference patches and test patches. The generation runner supplies the selected statement to the agent and prepares an isolated Base checkout. The evaluator reads the case test assets after the candidate is submitted.
