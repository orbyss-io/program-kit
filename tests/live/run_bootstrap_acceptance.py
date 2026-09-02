from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import IO


AGENT_ENVIRONMENT_KEYS = (
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
)
CI_ENVIRONMENT_KEYS = ("CI", "GITHUB_ACTIONS", "TF_BUILD", "BUILD_BUILDID")


class AcceptanceError(RuntimeError):
    pass


class QuietCatalogHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AcceptanceError(f"Expected a JSON object in {path}")
    return value


def run_logged(command: list[str], cwd: Path, log: IO[str]) -> None:
    printable = subprocess.list2cmdline(command)
    log.write(f"\n$ {printable}\n")
    log.flush()
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise AcceptanceError(f"Setup command exited with {result.returncode}: {printable}")


def safe_extract(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            try:
                target.relative_to(destination_root)
            except ValueError as exc:
                raise AcceptanceError(
                    f"Archive entry escapes extraction directory: {member.filename}"
                ) from exc
        archive.extractall(destination)


def prepare_local_catalog_server(
    root: Path,
    artifacts: Path,
    packages: Path,
    evidence: Path,
    version: str,
) -> tuple[http.server.ThreadingHTTPServer, threading.Thread, str]:
    server_root = evidence / "catalog-server"
    server_root.mkdir(parents=True, exist_ok=False)
    archive_names = {
        "governance": f"program-kit-governance-{version}.zip",
        "dotnet": f"program-kit-dotnet-{version}.zip",
        "preset": f"program-kit-governance-preset-{version}.zip",
    }
    for archive_name in archive_names.values():
        shutil.copy2(artifacts / archive_name, server_root / archive_name)
    shutil.copy2(packages / "workflow" / "workflow.yml", server_root / "workflow.yml")

    handler = functools.partial(QuietCatalogHandler, directory=str(server_root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    base_url = f"http://127.0.0.1:{server.server_port}"

    catalogs = {
        name: load_json(root / "catalogs" / f"{name}.json")
        for name in ("extensions", "presets", "workflows")
    }
    catalogs["extensions"]["catalog_url"] = f"{base_url}/extensions.json"
    catalogs["extensions"]["extensions"]["program-kit-governance"]["download_url"] = (
        f"{base_url}/{archive_names['governance']}"
    )
    catalogs["extensions"]["extensions"]["program-kit-dotnet"]["download_url"] = (
        f"{base_url}/{archive_names['dotnet']}"
    )
    catalogs["presets"]["catalog_url"] = f"{base_url}/presets.json"
    catalogs["presets"]["presets"]["program-kit-governance-preset"]["download_url"] = (
        f"{base_url}/{archive_names['preset']}"
    )
    catalogs["workflows"]["catalog_url"] = f"{base_url}/workflows.json"
    catalogs["workflows"]["workflows"]["program-kit-bootstrap"]["url"] = (
        f"{base_url}/workflow.yml"
    )
    for name, catalog in catalogs.items():
        write_json(server_root / f"{name}.json", catalog)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, base_url


def stream_pipe(pipe: IO[str], destination: Path, display: IO[str] | None = None) -> None:
    with destination.open("w", encoding="utf-8", newline="\n") as log:
        for line in iter(pipe.readline, ""):
            log.write(line)
            log.flush()
            if display is not None:
                display.write(line)
                display.flush()
    pipe.close()


def discover_run_state(project: Path) -> tuple[Path | None, dict | None]:
    candidates = sorted(
        (project / ".specify/workflows/runs").glob("*/state.json"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    if not candidates:
        return None, None
    path = candidates[0]
    try:
        return path, load_json(path)
    except (OSError, json.JSONDecodeError, AcceptanceError):
        return path, None


def append_monitor(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_worker_guidance(project: Path, integration: str) -> None:
    if integration != "codex":
        return
    safe_directory = project.resolve().as_posix()
    null_device = os.devnull.replace("\\", "/")
    guidance = f"""# Disposable live-acceptance worker guidance

This repository is owned by the Program Kit live acceptance harness and is safe to modify within
the requested bootstrap workflow. The Codex worker is intentionally launched with
`--sandbox workspace-write`.

Windows sandbox workers may see a different SID from the repository owner. For every Git command,
use the command-scoped form
`git -c safe.directory={safe_directory} -c core.excludesFile={null_device} <command>`. The null
exclude file prevents harmless permission warnings when the sandbox cannot read the user's global
Git ignore file. Never run `git config --global`, never disable the sandbox, and never add a
persistent safe-directory entry.

Use UTF-8 for Python subprocess output. Read compact bootstrap stage briefs first; do not print
complete evidence indexes, generated artifacts, or repository-wide diffs. Report concise counts,
paths, and validation results.
"""
    destination = project / "AGENTS.md"
    if destination.is_file():
        existing = destination.read_text(encoding="utf-8").rstrip()
        guidance = existing + "\n\n---\n\n" + guidance
    destination.write_text(guidance, encoding="utf-8", newline="\n")


def load_monitor(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def analyze_metrics(
    evidence: Path, run_id: str | None, workflow_duration: float | None = None
) -> dict:
    stderr_path = evidence / "workflow.stderr.log"
    stdout_path = evidence / "workflow.stdout.log"
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    token_values = [int(value.replace(",", "")) for value in re.findall(r"tokens used\s*[\r\n]+\s*([0-9,]+)", stderr_text)]
    agent_stages = (
        "normalize-design",
        "intake",
        "research",
        "constitution-draft",
        "architecture",
        "tooling",
        "specification-roadmap",
        "readiness",
    )
    monitor = load_monitor(evidence / "monitor.jsonl")
    observed_steps = {
        record.get("current_step_id")
        for record in monitor
        if isinstance(record.get("current_step_id"), str)
    }
    observed_agent_stages = [stage for stage in agent_stages if stage in observed_steps]
    stage_tokens = dict(zip(observed_agent_stages, token_values))
    unattributed_tokens = token_values[len(observed_agent_stages) :]
    stage_durations: dict[str, float] = {}
    for index, record in enumerate(monitor[:-1]):
        step = record.get("current_step_id")
        start = record.get("elapsed_seconds")
        end = monitor[index + 1].get("elapsed_seconds")
        if isinstance(step, str) and isinstance(start, (int, float)) and isinstance(end, (int, float)):
            stage_durations[step] = round(float(end) - float(start), 3)
    if monitor and workflow_duration is not None:
        final_record = monitor[-1]
        final_step = final_record.get("current_step_id")
        final_start = final_record.get("elapsed_seconds")
        if (
            final_record.get("status") == "running"
            and isinstance(final_step, str)
            and isinstance(final_start, (int, float))
            and workflow_duration > float(final_start)
        ):
            stage_durations[final_step] = round(workflow_duration - float(final_start), 3)
    contexts: dict[str, dict] = {}
    if run_id:
        context_root = evidence / "project/.specify/workflows/runs" / run_id / "program-kit-context"
        for path in sorted(context_root.glob("*.json")):
            label = path.name
            contexts[label] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    artifacts: dict[str, dict] = {}
    artifact_root = evidence / "project/docs/architecture"
    if artifact_root.is_dir():
        for path in sorted(item for item in artifact_root.rglob("*") if item.is_file()):
            label = path.relative_to(evidence / "project").as_posix()
            artifacts[label] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return {
        "agent_session_count": len(token_values),
        "agent_tokens_total": sum(token_values),
        "agent_tokens_by_stage": stage_tokens,
        "unattributed_agent_tokens": unattributed_tokens,
        "stage_duration_seconds": stage_durations,
        "workflow_stdout_bytes": stdout_path.stat().st_size if stdout_path.is_file() else 0,
        "workflow_stderr_bytes": stderr_path.stat().st_size if stderr_path.is_file() else 0,
        "contexts": contexts,
        "artifacts": artifacts,
    }


def performance_warnings(metrics: dict, budgets: dict) -> list[str]:
    warnings: list[str] = []
    total_budget = budgets.get("agent_tokens_total")
    if isinstance(total_budget, int) and metrics.get("agent_tokens_total", 0) > total_budget:
        warnings.append(
            f"Agent token total {metrics['agent_tokens_total']} exceeds advisory budget {total_budget}"
        )
    stderr_budget = budgets.get("workflow_stderr_bytes")
    if isinstance(stderr_budget, int) and metrics.get("workflow_stderr_bytes", 0) > stderr_budget:
        warnings.append(
            f"Workflow stderr {metrics['workflow_stderr_bytes']} bytes exceeds advisory budget {stderr_budget}"
        )
    context_budget = budgets.get("stage_brief_bytes")
    if isinstance(context_budget, int):
        for name, record in metrics.get("contexts", {}).items():
            if name.endswith(".evidence.json"):
                continue
            if record.get("bytes", 0) > context_budget:
                warnings.append(
                    f"Stage brief {name} is {record['bytes']} bytes; advisory budget is {context_budget}"
                )
    artifact_budgets = budgets.get("artifact_bytes", {})
    if isinstance(artifact_budgets, dict):
        for name, budget in artifact_budgets.items():
            record = metrics.get("artifacts", {}).get(name)
            if isinstance(budget, int) and record and record.get("bytes", 0) > budget:
                warnings.append(
                    f"Artifact {name} is {record['bytes']} bytes; advisory budget is {budget}"
                )
    return warnings


def terminate_owned_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def run_workflow(
    specify: str,
    project: Path,
    integration: str,
    evidence: Path,
    timeout_seconds: int,
) -> tuple[int, float, str | None]:
    command = [
        specify,
        "workflow",
        "run",
        "program-kit-bootstrap",
        "--input",
        "initial_design=./INITIAL_DESIGN.md",
        "--input",
        f"integration={integration}",
        "--input",
        "assessment_verdict=approve",
        "--input",
        "constitution_verdict=ratify",
        "--input",
        "bootstrap_verdict=approve",
        "--json",
    ]
    environment = os.environ.copy()
    removed = [key for key in AGENT_ENVIRONMENT_KEYS if environment.pop(key, None)]
    environment["PROGRAM_KIT_LIVE_ACCEPTANCE"] = "clean-bootstrap"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    worker_settings: dict[str, object] = {}
    if integration == "codex":
        environment["SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS"] = "--sandbox workspace-write"
        try:
            git_config_count = int(environment.get("GIT_CONFIG_COUNT", "0"))
        except ValueError as exc:
            raise AcceptanceError("GIT_CONFIG_COUNT must be an integer") from exc
        environment[f"GIT_CONFIG_KEY_{git_config_count}"] = "safe.directory"
        environment[f"GIT_CONFIG_VALUE_{git_config_count}"] = str(project)
        environment[f"GIT_CONFIG_KEY_{git_config_count + 1}"] = "core.excludesFile"
        environment[f"GIT_CONFIG_VALUE_{git_config_count + 1}"] = os.devnull
        environment["GIT_CONFIG_COUNT"] = str(git_config_count + 2)
        worker_settings = {
            "sandbox": "workspace-write",
            "git_safe_directory": str(project),
            "git_safe_directory_parent_scope": "workflow-process-only-best-effort",
            "git_safe_directory_worker_fallback": (
                f"git -c safe.directory={project.resolve().as_posix()} "
                f"-c core.excludesFile={os.devnull} <command>"
            ),
            "git_excludes_file_process_scope": os.devnull,
            "global_git_configuration_modified": False,
        }
    write_json(
        evidence / "invocation.json",
        {
            "command": command,
            "cwd": str(project),
            "integration": integration,
            "started_at": utc_now(),
            "agent_environment_keys_removed_from_disposable_child": removed,
            "worker_settings": worker_settings,
        },
    )
    process = subprocess.Popen(
        command,
        cwd=project,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    if process.stdout is None or process.stderr is None:
        terminate_owned_process(process)
        raise AcceptanceError("Could not capture workflow output streams")
    stdout_thread = threading.Thread(
        target=stream_pipe,
        args=(process.stdout, evidence / "workflow.stdout.log", sys.stdout),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=stream_pipe,
        args=(process.stderr, evidence / "workflow.stderr.log"),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    monitor = evidence / "monitor.jsonl"
    started = time.monotonic()
    last_state: tuple[object, ...] | None = None
    run_id: str | None = None
    try:
        while process.poll() is None:
            elapsed = time.monotonic() - started
            state_path, state = discover_run_state(project)
            if state:
                run_id = str(state.get("run_id") or state_path.parent.name)
                state_key = (
                    state.get("status"),
                    state.get("current_step_index"),
                    state.get("current_step_id"),
                )
                if state_key != last_state:
                    append_monitor(
                        monitor,
                        {
                            "timestamp": utc_now(),
                            "elapsed_seconds": round(elapsed, 3),
                            "process_id": process.pid,
                            "run_id": run_id,
                            "status": state_key[0],
                            "current_step_index": state_key[1],
                            "current_step_id": state_key[2],
                        },
                    )
                    print(
                        "Live bootstrap progress: "
                        f"step={state_key[2]} status={state_key[0]} elapsed={round(elapsed, 1)}s"
                    )
                    last_state = state_key
            if elapsed > timeout_seconds:
                append_monitor(
                    monitor,
                    {
                        "timestamp": utc_now(),
                        "elapsed_seconds": round(elapsed, 3),
                        "process_id": process.pid,
                        "event": "timeout",
                    },
                )
                terminate_owned_process(process)
                raise AcceptanceError(
                    f"Live bootstrap exceeded its {timeout_seconds}-second timeout"
                )
            time.sleep(2)
        return_code = process.wait()
        elapsed = time.monotonic() - started
        state_path, state = discover_run_state(project)
        if state:
            run_id = str(state.get("run_id") or state_path.parent.name)
            state_key = (
                state.get("status"),
                state.get("current_step_index"),
                state.get("current_step_id"),
            )
            if state_key != last_state:
                append_monitor(
                    monitor,
                    {
                        "timestamp": utc_now(),
                        "elapsed_seconds": round(elapsed, 3),
                        "process_id": process.pid,
                        "run_id": run_id,
                        "status": state_key[0],
                        "current_step_index": state_key[1],
                        "current_step_id": state_key[2],
                    },
                )
    except BaseException:
        terminate_owned_process(process)
        raise
    finally:
        stdout_thread.join(timeout=10)
        stderr_thread.join(timeout=10)
    return return_code, time.monotonic() - started, run_id


def install_candidate(
    root: Path,
    project: Path,
    packages: Path,
    integration: str,
    setup_log: Path,
) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    artifacts = root / "artifacts"
    archives = {
        "governance": artifacts / f"program-kit-governance-{version}.zip",
        "dotnet": artifacts / f"program-kit-dotnet-{version}.zip",
        "preset": artifacts / f"program-kit-governance-preset-{version}.zip",
        "workflow": artifacts / f"program-kit-bootstrap-{version}.zip",
        "bundle": artifacts / f"program-kit-{version}.zip",
    }
    with setup_log.open("w", encoding="utf-8", newline="\n") as log:
        run_logged([sys.executable, str(root / "scripts/build_release.py")], root, log)
        for name, archive in archives.items():
            if not archive.is_file():
                raise AcceptanceError(f"Candidate release archive was not built: {archive}")
            safe_extract(archive, packages / name)
        run_logged(["git", "init"], project, log)
        run_logged(
            [
                "specify",
                "init",
                ".",
                "--force",
                "--non-interactive",
                "--integration",
                integration,
                "--script",
                "py",
                "--ignore-agent-tools",
            ],
            project,
            log,
        )
        server, thread, base_url = prepare_local_catalog_server(
            root, artifacts, packages, setup_log.parent, version
        )
        try:
            run_logged(
                [
                    "specify",
                    "extension",
                    "catalog",
                    "add",
                    f"{base_url}/extensions.json",
                    "--name",
                    "program-kit-live-candidate",
                    "--priority",
                    "1",
                    "--install-allowed",
                ],
                project,
                log,
            )
            run_logged(
                [
                    "specify",
                    "preset",
                    "catalog",
                    "add",
                    f"{base_url}/presets.json",
                    "--name",
                    "program-kit-live-candidate",
                    "--priority",
                    "1",
                    "--install-allowed",
                ],
                project,
                log,
            )
            run_logged(
                [
                    "specify",
                    "workflow",
                    "catalog",
                    "add",
                    f"{base_url}/workflows.json",
                    "--name",
                    "program-kit-live-candidate",
                ],
                project,
                log,
            )
            # Spec Kit 1.0.1 requires the workflow to be preinstalled before
            # bundle installation. The remaining components are installed and
            # provenance-recorded by the real bundle machinery.
            run_logged(
                ["specify", "workflow", "add", "program-kit-bootstrap"],
                project,
                log,
            )
            run_logged(
                [
                    "specify",
                    "bundle",
                    "install",
                    str(archives["bundle"]),
                    "--integration",
                    integration,
                ],
                project,
                log,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=10)


def validate_result(
    root: Path,
    project: Path,
    expectations: dict,
    run_id: str | None,
    validation_log: Path,
) -> tuple[dict, list[str]]:
    failures: list[str] = []
    workflow_completed = False
    state_path, state = discover_run_state(project)
    if not state_path or not state:
        failures.append("No readable Spec Kit workflow state was produced")
        state = {}
    else:
        run_id = run_id or str(state.get("run_id") or state_path.parent.name)
        workflow_completed = state.get("status") == "completed"
        if not workflow_completed:
            failures.append(f"Workflow status is {state.get('status')!r}, expected 'completed'")
        failed_steps = [
            step_id
            for step_id, record in state.get("step_results", {}).items()
            if isinstance(record, dict) and record.get("status") != "completed"
        ]
        if failed_steps:
            failures.append(f"Workflow has non-completed steps: {failed_steps}")

    file_evidence: list[dict] = []
    for relative in expectations["required_files"]:
        path = project / relative
        if not path.is_file():
            if workflow_completed:
                failures.append(f"Required artifact is missing: {relative}")
            continue
        file_evidence.append(
            {"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)}
        )

    readiness = project / "docs/architecture/readiness-report.md"
    if readiness.is_file():
        first_line = readiness.read_text(encoding="utf-8").splitlines()[0]
        if workflow_completed and first_line != expectations["readiness_first_line"]:
            failures.append(
                f"Readiness first line is {first_line!r}, expected {expectations['readiness_first_line']!r}"
            )

    if run_id:
        context_root = project / ".specify/workflows/runs" / run_id / "program-kit-context"
        for stage in expectations["required_context_stages"]:
            for suffix in (".json", ".evidence.json"):
                path = context_root / f"{stage}{suffix}"
                if workflow_completed and not path.is_file():
                    failures.append(f"Bootstrap context is missing: {path.name}")

    validator = project / ".specify/extensions/program-kit-governance/scripts/governance_state.py"
    with validation_log.open("w", encoding="utf-8", newline="\n") as log:
        if workflow_completed and validator.is_file():
            result = subprocess.run(
                [
                    sys.executable,
                    str(validator),
                    "validate-bootstrap",
                    "--require-approval",
                    "--require-ready",
                ],
                cwd=project,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode != 0:
                failures.append(
                    f"Final governance validator exited with {result.returncode}; see validation.log"
                )
        elif workflow_completed:
            failures.append("Installed governance-state validator is missing")
        else:
            log.write("Final governance validation skipped because the workflow did not complete.\n")
    return {"run_id": run_id, "state": state, "files": file_evidence}, failures


def write_report(
    evidence: Path,
    scenario: str,
    integration: str,
    duration: float,
    workflow_exit_code: int | None,
    result: dict,
    failures: list[str],
    warnings: list[str],
) -> None:
    status = "passed" if workflow_exit_code == 0 and not failures else "failed"
    payload = {
        "schema_version": "1.1",
        "scenario": scenario,
        "integration": integration,
        "status": status,
        "duration_seconds": round(duration, 3),
        "workflow_exit_code": workflow_exit_code,
        "completed_at": utc_now(),
        "failures": failures,
        "warnings": warnings,
        "result": result,
    }
    write_json(evidence / "report.json", payload)
    lines = [
        "# Program Kit live bootstrap acceptance",
        "",
        f"- Status: **{status.upper()}**",
        f"- Scenario: `{scenario}`",
        f"- Integration: `{integration}`",
        f"- Duration: `{round(duration, 1)} seconds`",
        f"- Workflow exit code: `{workflow_exit_code}`",
        f"- Run ID: `{result.get('run_id')}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend(f"- {failure}" for failure in failures)
    if not failures:
        lines.append("- None")
    lines.extend(["", "## Performance observations", ""])
    lines.extend(f"- {warning}" for warning in warnings)
    if not warnings:
        lines.append("- All advisory budgets were met")
    metrics = result.get("metrics", {})
    if metrics:
        lines.extend(
            [
                "",
                f"- Agent sessions observed: `{metrics.get('agent_session_count', 0)}`",
                f"- Agent tokens observed: `{metrics.get('agent_tokens_total', 0)}`",
                f"- Captured stderr: `{metrics.get('workflow_stderr_bytes', 0)} bytes`",
            ]
        )
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "- `workflow.stdout.log`: structured workflow result.",
            "- `workflow.stderr.log`: live agent and gate output stream.",
            "- `monitor.jsonl`: workflow step transitions and elapsed time.",
            "- `validation.log`: final governance validation.",
            "- `project/`: preserved disposable consumer for diagnosis.",
            "",
        ]
    )
    (evidence / "report.md").write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the opt-in, API-consuming Program Kit bootstrap acceptance suite."
    )
    parser.add_argument("--scenario", default="clean-bootstrap", choices=("clean-bootstrap",))
    parser.add_argument("--integration", default="codex", choices=("codex", "claude"))
    parser.add_argument(
        "--approved",
        action="store_true",
        help="Confirm that the user explicitly approved this paid live agent run.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--output-root", default="artifacts/live-acceptance")
    args = parser.parse_args()

    if not args.approved:
        print(
            "LIVE_ACCEPTANCE_APPROVAL_REQUIRED: Ask the user whether to run the paid live "
            "bootstrap acceptance suite. Re-run with --approved only after an explicit yes.",
            file=sys.stderr,
        )
        return 3
    active_ci = [key for key in CI_ENVIRONMENT_KEYS if os.environ.get(key)]
    if active_ci:
        print(
            "LIVE_ACCEPTANCE_CI_FORBIDDEN: This paid agentic suite must not run in CI "
            f"({', '.join(active_ci)} is set).",
            file=sys.stderr,
        )
        return 3
    if args.timeout_seconds < 60:
        print("Live acceptance timeout must be at least 60 seconds.", file=sys.stderr)
        return 3
    specify = shutil.which("specify")
    integration_cli = shutil.which(args.integration)
    if not specify or not integration_cli:
        print(
            f"Required CLI is missing: specify={specify!r}, {args.integration}={integration_cli!r}",
            file=sys.stderr,
        )
        return 3

    root = Path(__file__).resolve().parents[2]
    scenario_root = Path(__file__).resolve().parent / "scenarios" / args.scenario
    expectations = load_json(scenario_root / "expectations.json")
    output_root = (root / args.output_root).resolve()
    try:
        output_root.relative_to(root)
    except ValueError:
        print("Live acceptance output must stay inside the Program Kit repository.", file=sys.stderr)
        return 3
    identifier = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-{args.scenario}-{args.integration}-{uuid.uuid4().hex[:6]}"
    )
    evidence = output_root / identifier
    project = evidence / "project"
    packages = evidence / "packages"
    project.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(scenario_root / "INITIAL_DESIGN.md", project / "INITIAL_DESIGN.md")
    print(f"Live acceptance evidence: {evidence}")

    started = time.monotonic()
    workflow_exit_code: int | None = None
    workflow_duration: float | None = None
    run_id: str | None = None
    failures: list[str] = []
    result: dict = {}
    try:
        install_candidate(
            root,
            project,
            packages,
            args.integration,
            evidence / "setup.log",
        )
        write_worker_guidance(project, args.integration)
        workflow_exit_code, workflow_duration, run_id = run_workflow(
            specify,
            project,
            args.integration,
            evidence,
            args.timeout_seconds,
        )
        if workflow_exit_code != 0:
            failures.append(f"Workflow process exited with {workflow_exit_code}")
        result, validation_failures = validate_result(
            root,
            project,
            expectations,
            run_id,
            evidence / "validation.log",
        )
        failures.extend(validation_failures)
    except KeyboardInterrupt:
        failures.append("Live bootstrap was interrupted by the operator")
        state_path, state = discover_run_state(project)
        result = {
            "run_id": state.get("run_id") if state else run_id,
            "state_path": str(state_path) if state_path else None,
            "state": state or {},
            "files": [],
        }
    except (AcceptanceError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
        state_path, state = discover_run_state(project)
        result = {
            "run_id": state.get("run_id") if state else run_id,
            "state_path": str(state_path) if state_path else None,
            "state": state or {},
            "files": [],
        }
    resolved_run_id = str(result.get("run_id") or run_id or "") or None
    metrics = analyze_metrics(evidence, resolved_run_id, workflow_duration)
    warnings = performance_warnings(metrics, expectations.get("advisory_budgets", {}))
    if workflow_exit_code not in (None, 0):
        warnings.insert(0, "Performance observations are partial because the workflow failed")
    result["metrics"] = metrics
    duration = time.monotonic() - started
    write_report(
        evidence,
        args.scenario,
        args.integration,
        duration,
        workflow_exit_code,
        result,
        failures,
        warnings,
    )
    print(f"Live acceptance report: {evidence / 'report.md'}")
    return 0 if workflow_exit_code == 0 and not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
