from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

import yaml


def load_module(root: Path):
    path = (
        root
        / "extensions/program-kit-governance/scripts/codex_bootstrap_preflight.py"
    )
    spec = importlib.util.spec_from_file_location("codex_bootstrap_preflight", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    module = load_module(root)

    matching = [
        ["specify", "workflow", "run", "program-kit-bootstrap"],
        [
            "specify",
            "workflow",
            "run",
            "program-kit-bootstrap",
            "--input",
            "initial_design=./INITIAL_DESIGN.md",
        ],
    ]
    not_matching = [
        ["specify", "workflow", "run", "unrelated-workflow"],
        ["specify", "workflow", "resume", "program-kit-bootstrap"],
        ["specify", "workflow"],
        ["powershell", "-Command", "specify workflow run program-kit-bootstrap"],
    ]
    for argv in matching:
        if not module.matches_bootstrap_prefix(argv):
            raise AssertionError(f"Expected bootstrap prefix match: {argv}")
    for argv in not_matching:
        if module.matches_bootstrap_prefix(argv):
            raise AssertionError(f"Unexpected bootstrap prefix match: {argv}")

    with tempfile.TemporaryDirectory(prefix="program-kit-codex-preflight-") as temp:
        project = Path(temp)
        specify = project / ".specify"
        specify.mkdir()
        (specify / "integration.json").write_text(
            json.dumps({"default_integration": "codex"}), encoding="utf-8"
        )
        if module.resolve_integration("auto", project) != "codex":
            raise AssertionError("auto did not resolve the initialized Codex integration")
        if module.resolve_integration("claude", project) != "claude":
            raise AssertionError("explicit integration should win over project config")

    codex_env = {"CODEX_SESSION_ID": "test-session"}
    if not module.is_nested_codex_sandbox_unavailable(
        integration="codex",
        platform_name="nt",
        current_user="CodexSandboxOffline",
        environ=codex_env,
    ):
        raise AssertionError("Native Windows elevated Codex sandbox was not detected")
    for case in (
        dict(
            integration="claude",
            platform_name="nt",
            current_user="CodexSandboxOffline",
            environ=codex_env,
        ),
        dict(
            integration="codex",
            platform_name="posix",
            current_user="codexsandboxoffline",
            environ=codex_env,
        ),
        dict(
            integration="codex",
            platform_name="nt",
            current_user="ordinary-user",
            environ=codex_env,
        ),
        dict(
            integration="codex",
            platform_name="nt",
            current_user="CodexSandboxOffline",
            environ={},
        ),
    ):
        if module.is_nested_codex_sandbox_unavailable(**case):
            raise AssertionError(f"False positive in preflight case: {case}")

    message = module.diagnostic()
    for phrase in (
        "PROGRAM_KIT_CODEX_NESTED_SANDBOX",
        "specify workflow run program-kit-bootstrap",
        "Always allow",
        "specify workflow resume",
        "ordinary PowerShell",
        "danger-full-access",
    ):
        if phrase not in message:
            raise AssertionError(f"Diagnostic is missing actionable text: {phrase}")

    rules = (
        root
        / "extensions/program-kit-governance/templates/codex/program-kit-bootstrap.rules"
    ).read_text(encoding="utf-8")
    for phrase in (
        'pattern = ["specify", "workflow", "run", "program-kit-bootstrap"]',
        'decision = "allow"',
        "match = [",
        "not_match = [",
        "specify workflow resume",
        "unrelated-workflow",
    ):
        if phrase not in rules:
            raise AssertionError(f"Rules template is missing: {phrase}")

    workflow = yaml.safe_load(
        (root / "workflows/program-kit-bootstrap/workflow.yml").read_text(
            encoding="utf-8"
        )
    )
    first = workflow["steps"][0]
    if first.get("id") != "codex-execution-preflight" or first.get("type") != "shell":
        raise AssertionError("Codex preflight must run before every agent-dispatched step")
    if "codex_bootstrap_preflight.py" not in first.get("run", ""):
        raise AssertionError("Workflow preflight does not invoke its diagnostic")
    if "{{" in first.get("run", ""):
        raise AssertionError("Workflow preflight must not interpolate user input into a shell")
    if first.get("output_format") != "json" or "--json" not in first.get("run", ""):
        raise AssertionError("Workflow preflight must expose a structured switch action")
    boundary = workflow["steps"][1]
    if boundary.get("id") != "codex-execution-boundary" or boundary.get("type") != "switch":
        raise AssertionError("Structured preflight must be followed by its execution boundary")
    blocked = boundary.get("cases", {}).get("blocked", [])
    if len(blocked) != 1:
        raise AssertionError("Blocked preflight must have exactly one diagnostic failure step")
    error_command = blocked[0].get("command", "")
    for phrase in (
        "PROGRAM_KIT_CODEX_NESTED_SANDBOX",
        "outside the sandbox",
        "specify workflow run program-kit-bootstrap",
        "ordinary PowerShell",
        "Keep resume prompted",
    ):
        if phrase not in error_command:
            raise AssertionError(f"Workflow-visible diagnostic is missing: {phrase}")

    skill = (
        root
        / "extensions/program-kit-governance/commands/speckit.program-kit-governance.bootstrap.md"
    ).read_text(encoding="utf-8")
    for phrase in (
        "Do not first attempt",
        "outside the current task sandbox",
        "first four argument tokens",
        "Never propose `specify workflow`",
        "Do not install a Codex rule silently",
    ):
        if phrase not in skill:
            raise AssertionError(f"Bootstrap skill is missing: {phrase}")

    print("Codex Desktop bootstrap boundary and diagnostics are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
