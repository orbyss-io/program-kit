from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from live.run_bootstrap_acceptance import (
    analyze_metrics,
    performance_warnings,
    validate_result,
)


def run_guard(runner: Path, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        [sys.executable, str(runner), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def require(path: Path, *phrases: str) -> None:
    text = " ".join(path.read_text(encoding="utf-8").split())
    missing = [phrase for phrase in phrases if " ".join(phrase.split()) not in text]
    if missing:
        raise AssertionError(f"{path} is missing live-acceptance policy text: {missing}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    runner = root / "tests/live/run_bootstrap_acceptance.py"
    wrapper = root / "scripts/Test-LiveBootstrap.ps1"
    scenario = root / "tests/live/scenarios/clean-bootstrap"
    for path in (
        runner,
        wrapper,
        scenario / "INITIAL_DESIGN.md",
        scenario / "expectations.json",
        root / "docs/live-bootstrap-acceptance.md",
        root / "AGENTS.md",
    ):
        if not path.is_file():
            raise AssertionError(f"Live bootstrap acceptance component is missing: {path}")

    with tempfile.TemporaryDirectory(prefix="program-kit-live-guard-") as directory:
        denied = run_guard(runner, "--output-root", directory)
        if denied.returncode != 3 or "LIVE_ACCEPTANCE_APPROVAL_REQUIRED" not in denied.stderr:
            raise AssertionError(f"Unapproved live run was not refused: {denied}")
        if any(Path(directory).iterdir()):
            raise AssertionError("Unapproved live run created output before refusing")

    with tempfile.TemporaryDirectory(prefix="program-kit-live-metrics-") as directory:
        evidence = Path(directory)
        (evidence / "workflow.stderr.log").write_text(
            "tokens used\n1,200\ntokens used\n300\n", encoding="utf-8"
        )
        (evidence / "workflow.stdout.log").write_text("{}\n", encoding="utf-8")
        monitor = [
            {"status": "running", "current_step_id": "intake", "elapsed_seconds": 2.0},
            {"status": "running", "current_step_id": "research", "elapsed_seconds": 7.0},
        ]
        (evidence / "monitor.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in monitor), encoding="utf-8"
        )
        metrics = analyze_metrics(evidence, None, workflow_duration=10.0)
        if metrics["agent_tokens_by_stage"] != {"intake": 1200, "research": 300}:
            raise AssertionError(f"Agent token attribution is invalid: {metrics}")
        if metrics["stage_duration_seconds"] != {"intake": 5.0, "research": 3.0}:
            raise AssertionError(f"Stage duration attribution is invalid: {metrics}")
        if performance_warnings(metrics, {"agent_tokens_total": 1000}) != [
            "Agent token total 1500 exceeds advisory budget 1000"
        ]:
            raise AssertionError("Live advisory budgets are not reported predictably")

    with tempfile.TemporaryDirectory(prefix="program-kit-live-failure-") as directory:
        project = Path(directory)
        state_path = project / ".specify/workflows/runs/failed-run/state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(
            json.dumps(
                {
                    "run_id": "failed-run",
                    "status": "failed",
                    "step_results": {"research": {"status": "failed"}},
                }
            ),
            encoding="utf-8",
        )
        _, failures = validate_result(
            root,
            project,
            {
                "required_files": ["downstream.md"],
                "required_context_stages": ["readiness"],
                "readiness_first_line": "**Status**: READY",
            },
            "failed-run",
            project / "validation.log",
        )
        if failures != [
            "Workflow status is 'failed', expected 'completed'",
            "Workflow has non-completed steps: ['research']",
        ]:
            raise AssertionError(f"Failed live report cascaded downstream noise: {failures}")

    ci_environment = os.environ.copy()
    ci_environment["CI"] = "true"
    denied_ci = run_guard(runner, "--approved", env=ci_environment)
    if denied_ci.returncode != 3 or "LIVE_ACCEPTANCE_CI_FORBIDDEN" not in denied_ci.stderr:
        raise AssertionError(f"CI live run was not refused: {denied_ci}")

    expectations = json.loads((scenario / "expectations.json").read_text(encoding="utf-8"))
    if expectations.get("scenario") != "clean-bootstrap":
        raise AssertionError("Clean-bootstrap expectations have the wrong scenario ID")
    if expectations.get("readiness_first_line") != "**Status**: READY":
        raise AssertionError("Clean-bootstrap scenario does not require exact READY evidence")
    stages = expectations.get("required_context_stages")
    if stages != ["research", "architecture", "tooling", "roadmap", "readiness"]:
        raise AssertionError(f"Live scenario context coverage is incomplete: {stages}")
    budgets = expectations.get("advisory_budgets", {})
    scalar_budgets = {
        key: value for key, value in budgets.items() if key != "artifact_bytes"
    }
    artifact_budgets = budgets.get("artifact_bytes", {})
    if (
        not all(isinstance(value, int) and value > 0 for value in scalar_budgets.values())
        or not isinstance(artifact_budgets, dict)
        or not all(isinstance(value, int) and value > 0 for value in artifact_budgets.values())
    ):
        raise AssertionError(f"Live scenario advisory budgets are invalid: {budgets}")

    require(
        root / "AGENTS.md",
        "entirely user-invoked",
        "Do not ask",
        "do not report it as skipped",
        "Never add the paid live suite to CI",
        "Never pass `-Approved` without an explicit user request",
    )
    policy_files = (
        root / "AGENTS.md",
        root / "README.md",
        root / "docs/live-bootstrap-acceptance.md",
        root / "docs/releasing-0.8.1.md",
        root / "docs/releasing-0.8.2.md",
        root / "docs/releasing-0.8.3.md",
        wrapper,
        runner,
    )
    forbidden_policy = (
        "Do you want me to run the paid live bootstrap acceptance suite before publishing",
        "Before publishing, ask the user",
        "If the user answers no",
        "explicitly skipped",
        "record that explicit skip",
    )
    for policy_file in policy_files:
        policy_text = policy_file.read_text(encoding="utf-8")
        for forbidden in forbidden_policy:
            if forbidden in policy_text:
                raise AssertionError(
                    f"{policy_file} restores a forbidden publication prompt: {forbidden}"
                )
    require(
        root / "README.md",
        "completely optional and user-invoked",
        "Publishing must not prompt for it or record it as skipped",
    )
    require(
        root / "docs/live-bootstrap-acceptance.md",
        "entirely user-invoked",
        "publication must not prompt for it",
        "clean-bootstrap",
        "real bundle provenance machinery",
        "workflow.stdout.log",
        "workflow.stderr.log",
        "monitor.jsonl",
        "Failed runs are retained",
        "must not be generalized",
        "command-scoped",
        "git -c safe.directory",
        "core.excludesFile",
        "never changes global Git configuration",
        "advisory",
        "Could not find home directory",
        "outer harness process",
        "inner `--sandbox workspace-write`",
    )
    require(
        wrapper,
        "LIVE_ACCEPTANCE_APPROVAL_REQUIRED",
        "only when the user explicitly requests",
        "publication must not prompt",
        "LIVE_ACCEPTANCE_CI_FORBIDDEN",
        "--approved",
    )
    require(
        runner,
        "after an explicit user request",
        "127.0.0.1",
        "bundle",
        "install",
        "program-kit-live-candidate",
        "--sandbox workspace-write",
        "safe.directory",
        "core.excludesFile",
        "write_worker_guidance",
        "PYTHONUTF8",
        "analyze_metrics",
        ".evidence.json",
        "server.shutdown()",
    )
    print("Live bootstrap acceptance request, CI, fixture, and evidence contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
