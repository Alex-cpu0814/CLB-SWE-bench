"""Run one public CLB task using mini-SWE-agent 2.0.0."""

import argparse
from getpass import getpass
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

from runtime import checked_file, docker_output, ensure_image, load_index, read_json, write_json


AGENT = Path(__file__).resolve().parent
TASKS = AGENT.parent / "tasks"


def run_case(case, task, directory, docker, image_id, *, key=None, preflight=False):
    if importlib.metadata.version("mini-swe-agent") != "2.0.0":
        raise RuntimeError("Install the pinned mini-SWE-agent 2.0.0 dependencies")
    with TemporaryDirectory(prefix="clb-agent-config-") as config_dir:
        os.environ["MSWEA_GLOBAL_CONFIG_DIR"] = config_dir
        os.environ["MSWEA_SILENT_STARTUP"] = "1"
        os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
        return run_isolated(case, task, directory, docker, image_id, key, preflight)


def run_isolated(case, task, directory, docker, image_id, key, preflight):
    from minisweagent.agents.default import DefaultAgent
    from minisweagent.environments.docker import DockerEnvironment
    from minisweagent.models.litellm_model import LitellmModel

    class ContainerEnvironment(DockerEnvironment):
        def cleanup(self):
            identifier = self.container_id
            if identifier is None:
                return
            self.container_id = None
            if not re.fullmatch(r"[0-9a-f]{64}", identifier):
                raise RuntimeError("Unexpected container ID")
            docker_output(docker, "rm", "-f", identifier, timeout=30)

    class PrivateKeyModel(LitellmModel):
        def _query(self, messages, **kwargs):
            return super()._query(messages, api_key=key, **kwargs)

        def _calculate_cost(self, response):
            usage = response.usage.model_dump() if getattr(response, "usage", None) else {}
            if any(type(usage.get(field)) is not int or usage[field] < 0 for field in
                   ("prompt_tokens", "completion_tokens", "total_tokens")):
                raise RuntimeError("Provider did not return usable token counts")
            return super()._calculate_cost(response)

    class RedactedTrajectoryAgent(DefaultAgent):
        def save(self, path, *extra_dicts):
            data = json.dumps(self.serialize(*extra_dicts), ensure_ascii=False)
            if key:
                data = data.replace(json.dumps(key, ensure_ascii=False)[1:-1], "[API_KEY_REDACTED]")
            value = json.loads(data)
            if path:
                write_json(path, value)
            return value

    config = read_json(AGENT / "config.json")
    environment = config["environment"]
    environment.pop("environment_class")
    is_java = case["cohort"].startswith("java_")
    limits = ["--cpus", "2", "--memory", "3g", "--memory-swap", "3g", "--pids-limit", "512"] if is_java else []
    env = ContainerEnvironment(**environment, image=image_id, executable=docker,
                               forward_env=[], run_args=["--rm", "--pull=never", "--network", "none",
                                                         "--label", "clb.delivery=v1", "--ulimit", "core=0", *limits])
    try:
        audit = prepare_base(env, case, docker, is_java)
        write_json(directory / "source_isolation.json", audit)
        if preflight:
            return 0
        config["model"]["litellm_model_registry"] = str(AGENT / "model_registry.json")
        model = PrivateKeyModel(**config["model"])
        agent = RedactedTrajectoryAgent(model, env, **config["agent"], output_path=directory / "trajectory.json")
        result = agent.run(task["problem_statement"])
        submission = result.get("submission", "")
        submitted = result.get("exit_status") == "Submitted" and bool(submission.strip())
        if submitted:
            if key and key in submission:
                raise RuntimeError("The candidate contained a reflected credential")
            (directory / "model_patch.diff").write_bytes(submission.encode("utf-8"))
        write_json(directory / "generation.json", {"instance_id": case["instance_id"],
                   "exit_status": result.get("exit_status"), "candidate_saved": submitted,
                   "model_calls": agent.n_calls, "reference_usd": agent.cost})
        return 0 if submitted else 1
    finally:
        env.cleanup()


def prepare_base(env, case, docker, is_java):
    cid = env.container_id
    inspect = json.loads(docker_output(docker, "inspect", cid))[0]
    host = inspect["HostConfig"]
    if inspect["Mounts"] or host["NetworkMode"] != "none" or host["Privileged"]:
        raise RuntimeError("Generation container isolation check failed")
    image_env = inspect["Config"]["Env"] or []
    if any(item.partition("=")[0].upper().endswith(("API_KEY", "TOKEN", "SECRET")) for item in image_env):
        raise RuntimeError("Credential-like variable in the Base image")
    interpreter = case["generation_python"]
    if is_java:
        settings = (host["Memory"], host["MemorySwap"], host["NanoCpus"], host["PidsLimit"])
        if settings != (3 * 1024**3, 3 * 1024**3, 2000000000, 512):
            raise RuntimeError("Java resource limits were not enforced")
        interpreter = docker_output(docker, "exec", cid, "bash", "-c",
                                    'command -v python || command -v python3 || command -v python2.7')
        if not re.fullmatch(r"/[A-Za-z0-9_./+-]+", interpreter):
            raise RuntimeError("Invalid image interpreter")
    helper = AGENT / ("javac_clean_source.py" if is_java else "formal_clean_source.py")
    remote = "/tmp/clb-release-clean-source.py"
    docker_output(docker, "cp", helper, cid + ":" + remote)
    arguments = ["--case", case["case"]] if is_java else []
    audit = json.loads(docker_output(docker, "exec", cid, interpreter, remote,
                                    case["base_commit"], *arguments, timeout=240))
    cleanup_user = ["--user", "0"] if case["case"] == "javac_case_200" else []
    docker_output(docker, "exec", *cleanup_user, cid, "rm", remote)
    if case["case"] == "javac_case_200" and docker_output(docker, "exec", cid, "id", "-u") != "64":
        raise RuntimeError("Java 200 must run as UID 64")
    if case["case"] == "javac_case_075":
        env.config.env["KOTLIN_HOME"] = "/opt/base-dependencies/kotlinc"
    if not is_java and interpreter != "python":
        if not re.fullmatch(r"python[0-9.]+(?:-dbg)?", interpreter):
            raise RuntimeError("Invalid Python runtime profile")
        docker_output(docker, "exec", cid, "bash", "-c",
                      f'mkdir -p /opt/formal-python/bin && ln -s "$(command -v {interpreter})" /opt/formal-python/bin/python')
        original = next((item[5:] for item in image_env if item.startswith("PATH=")), "/usr/local/bin:/usr/bin:/bin")
        env.config.env["PATH"] = "/opt/formal-python/bin:" + original
    return audit | {"image_id": env.config.image, "network": host["NetworkMode"], "mounts": inspect["Mounts"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("instance_id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--docker", default="docker")
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="Verify the Base container without calling a model")
    args = parser.parse_args()
    key = None
    try:
        case = load_index(TASKS / "index.json")[args.instance_id]
        task = read_json(checked_file(TASKS, case["task"]))
        image_id = ensure_image(args.docker, case["image"], args.pull)
        if not args.preflight:
            key = os.getenv("CLB_MODEL_API_KEY") or getpass("Model API key: ")
            if not key:
                raise ValueError("A model API key is required")
        directory = args.output_dir.resolve()
        directory.mkdir(parents=True, exist_ok=False)
        return run_case(case, task, directory, args.docker, image_id, key=key, preflight=args.preflight)
    except (Exception, KeyboardInterrupt) as error:
        message = str(error)
        if key:
            message = message.replace(key, "[API_KEY_REDACTED]")
        print(f"{type(error).__name__}: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
