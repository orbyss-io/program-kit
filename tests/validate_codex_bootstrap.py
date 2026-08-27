from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

import yaml


FORBIDDEN_WORKAROUND_PHRASES = (
    "Always allow",
    "first four argument tokens",
    "program-kit-bootstrap.rules",
    "codex execpolicy",
    "approve only this exact prefix",
)


def load_module(root: Path):
    path = root / "extensions/program-kit-governance/scripts/codex_bootstrap_preflight.py"
    spec = importlib.util.spec_from_file_location("codex_bootstrap_preflight", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_phrases(label: str, text: str, phrases: tuple[str, ...]) -> None:
    normalized_text = " ".join(text.split())
    for phrase in phrases:
        if " ".join(phrase.split()) not in normalized_text:
            raise AssertionError(f"{label} is missing actionable text: {phrase}")


def reject_workaround(label: str, text: str) -> None:
    normalized_text = " ".join(text.split())
    for phrase in FORBIDDEN_WORKAROUND_PHRASES:
        if " ".join(phrase.split()) in normalized_text:
            raise AssertionError(f"{label} reintroduced the escalation workaround: {phrase}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    extension_root = root / "extensions/program-kit-governance"
    module = load_module(root)

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

    for key in module.CODEX_AGENT_ENVIRONMENT_KEYS:
        if not module.is_codex_agent_invocation(
            integration="codex", environ={key: "test-value"}
        ):
            raise AssertionError(f"Codex agent environment was not detected from {key}")
    for case in (
        {"integration": "claude", "environ": {"CODEX_SESSION_ID": "test"}},
        {"integration": "codex", "environ": {}},
    ):
        if module.is_codex_agent_invocation(**case):
            raise AssertionError(f"False positive in preflight case: {case}")

    message = module.diagnostic()
    require_phrases(
        "Preflight diagnostic",
        message,
        (
            "PROGRAM_KIT_CODEX_AGENT_BOUNDARY",
            "normal PowerShell or WSL terminal",
            "run the full command there",
            "interactive Codex CLI agent",
            "dedicated lower-privilege identities",
            "`.agents`",
            "rerunning init alone may not repair ownership",
            "Do not ask this agent",
        ),
    )
    reject_workaround("Preflight diagnostic", message)

    rule_files = list(extension_root.rglob("*.rules"))
    if rule_files:
        raise AssertionError(f"Extension must not package Codex approval rules: {rule_files}")

    workflow = yaml.safe_load(
        (root / "workflows/program-kit-bootstrap/workflow.yml").read_text(encoding="utf-8")
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
    require_phrases(
        "Workflow-visible diagnostic",
        error_command,
        (
            "PROGRAM_KIT_CODEX_AGENT_BOUNDARY",
            "normal user-owned PowerShell or WSL terminal",
            "interactive Codex CLI agent",
            "Do not ask the agent",
            "rerunning init alone may not repair ownership",
        ),
    )
    reject_workaround("Workflow-visible diagnostic", error_command)

    skill = (
        extension_root / "commands/speckit.program-kit-governance.bootstrap.md"
    ).read_text(encoding="utf-8")
    require_phrases(
        "Bootstrap skill",
        skill,
        (
            "This skill is guidance-only",
            "normal user-owned PowerShell or WSL terminal",
            "Stop. Do not call a shell tool",
            "A Codex CLI agent is sandboxed too",
            "rerunning `specify init` alone may not repair",
        ),
    )
    reject_workaround("Bootstrap skill", skill)

    packaged_reference = (
        extension_root / "references/codex-desktop-windows.md"
    ).read_text(encoding="utf-8")
    require_phrases(
        "Packaged Windows reference",
        packaged_reference,
        (
            "normal user-owned PowerShell or WSL",
            "dedicated lower-privilege users",
            "SetNamedSecurityInfoW ... error 5",
            "git clone --no-hardlinks --no-checkout",
            "Preserve `.git`",
        ),
    )
    reject_workaround("Packaged Windows reference", packaged_reference)

    root_guidance = (root / "docs/codex-desktop-windows.md").read_text(encoding="utf-8")
    require_phrases(
        "Root Windows guide",
        root_guidance,
        (
            "normal user-owned PowerShell or WSL shell",
            "SetNamedSecurityInfoW ... error 5",
            "Rerunning `specify init` is not an ownership repair",
            "Copy only the backed-up `INITIAL_DESIGN.md`",
            "Preserve `.git`",
        ),
    )
    reject_workaround("Root Windows guide", root_guidance)

    print("Codex agent bootstrap boundary and packaged guidance are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
