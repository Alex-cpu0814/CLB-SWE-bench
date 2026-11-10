# CLB SWE-bench

CLB SWE-bench evaluates software repair on 72 cross-language bugs. The test split includes 50 Python-C tasks, 11 Java-C tasks with upstream-derived tests, and 11 Java-C tasks with tests written by the CLB authors.

Each task uses a pinned Docker image and a Base commit. Use the same CLB instance ID for generation and evaluation. [Hugging Face dataset](https://huggingface.co/datasets/Alex-cpu0814/CLB-SWE-bench) · [Pinned dataset revision](https://huggingface.co/datasets/Alex-cpu0814/CLB-SWE-bench/tree/5f989e1e953a4e8f9071918643f36d439fc3d66c)

## Setup

Use Python 3.12 in a virtual environment and Docker configured for Linux containers. The task checkout contains `tasks/index.json` and `evaluation/index.json`. Use a trusted checkout because the harness executes its case evaluators.

Clone the code and check out the [matching task revision](https://github.com/Alex-cpu0814/CLB-SWE-bench-tasks/tree/5400a49b61d33ac0a8bbea0aaeab8b270e2cbed4). If you use a different task directory, substitute its path in the examples below.

```bash
git clone https://github.com/Alex-cpu0814/CLB-SWE-bench.git
cd CLB-SWE-bench
git clone https://github.com/Alex-cpu0814/CLB-SWE-bench-tasks.git ../CLB-SWE-bench-tasks
git -C ../CLB-SWE-bench-tasks checkout --detach 5400a49b61d33ac0a8bbea0aaeab8b270e2cbed4
```

From the code repository root, install the CLI and check the task checkout.

```bash
python -m pip install -e .
clb dataset check ../CLB-SWE-bench-tasks
```

## Verify with a reference patch

Run a Gold Patch against a fresh Base container. This uses Docker and requires no model API key.

```bash
clb eval run clb-pyc-086 --task-repo ../CLB-SWE-bench-tasks --pull --patch ../CLB-SWE-bench-tasks/gold/clb-pyc-086.diff --output-root grading --run-id case086-gold
```

Read `grading/case086-gold/summary.json`. The expected result is `resolved` with 2 of 2 target tests and 2 of 2 regression tests passing.

## Generate and evaluate a candidate

Install the pinned mini-SWE-agent dependencies and verify the Base before calling a model.

```bash
python -m pip install -e ".[infer]"
clb infer clb-pyc-086 --task-repo ../CLB-SWE-bench-tasks --pull --preflight --output-dir runs/case086-preflight
```

The Base preflight, dataset checks, and evaluation of existing patches, including Gold Patches, require no model API key.

### Run inference

Select the provider and model in the agent configuration. Use the key for that provider. Generation can incur model charges. [Agent configuration](agent/config.json)

For an interactive run, leave `CLB_MODEL_API_KEY` unset and enter your key at the `Model API key:` prompt. The terminal hides your input.

```bash
clb infer clb-pyc-086 --task-repo ../CLB-SWE-bench-tasks --pull --output-dir runs/case086-generation
```

For scripts or CI, expose the model secret as `CLB_MODEL_API_KEY` before running the same command. When this variable has a value, the CLI uses it without prompting. If your runner already exposes the secret as `PROVIDER_API_KEY`, map it to CLB's variable as shown below.

Set the variable in Bash.

```bash
export CLB_MODEL_API_KEY="${PROVIDER_API_KEY:?Set PROVIDER_API_KEY first}"
```

Set the variable in PowerShell.

```powershell
if (-not $env:PROVIDER_API_KEY) { throw "Set PROVIDER_API_KEY first" }
$env:CLB_MODEL_API_KEY = $env:PROVIDER_API_KEY
```

### Score the submitted patch

A successful submission writes `model_patch.diff` in the inference output directory.

```bash
clb eval run clb-pyc-086 --task-repo ../CLB-SWE-bench-tasks --pull --patch runs/case086-generation/model_patch.diff --output-root grading --run-id case086-first
```

The agent receives the selected statement and an isolated Base checkout. Evaluation reads the case test assets after the candidate is submitted. Use fresh output directories and run IDs. The evaluator returns 0 for resolved, 1 for unresolved, and 2 for an error. The per-case report is `summary.json` under the run directory.

## Evaluate a batch

Prepare `predictions.jsonl` with one record per line. Each record contains `instance_id` and `model_patch`, with the patch as a JSON string. An empty or null patch counts as a missing submission.

```bash
clb eval batch --task-repo ../CLB-SWE-bench-tasks --predictions predictions.jsonl --pull --output-root grading --run-id model-first-batch
```

The batch writes `grading/model-first-batch/summary.json` with paths to per-case reports.

## Repository layout

| Directory | Contents |
| --- | --- |
| [clb_swebench/](clb_swebench/cli.py) | Installable command-line interface |
| [agent/](agent/run.py) | mini-SWE-agent launcher and Base workspace preparation |
| [harness/](harness/evaluate.py) | Evaluation harness and shared Python-C runner |
| [collect/](collect/README.md) | Case selection checks, Base derivation, and patch extraction |
