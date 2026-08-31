from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

import yaml


FORBIDDEN_WORKAROUND_PHRASES = (
    "Always allow",
    "first four argument tokens",
    "program-kit-bootstrap.rules",
    "codex execpolicy",
    "approve only this exact prefix",
    "Set-ExecutionPolicy Bypass",
    "-ExecutionPolicy Bypass",
    "Unblock-File",
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
            raise AssertionError(f"{label} reintroduced an unsafe workaround: {phrase}")


def initialize_python_consumer(project: Path) -> None:
    subprocess.run(
        [
            "specify",
            "init",
            ".",
            "--force",
            "--non-interactive",
            "--integration",
            "codex",
            "--script",
            "py",
            "--ignore-agent-tools",
        ],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def validate_python_consumer(module) -> None:
    with tempfile.TemporaryDirectory(prefix="program-kit-python-consumer-") as temp:
        project = Path(temp)
        initialize_python_consumer(project)
        resolver = project / module.PYTHON_RESOLVER
        skill = project / module.CONSTITUTION_SKILL
        if not resolver.is_file():
            raise AssertionError("Python-flavor initialization did not install resolve_template.py")
        skill_text = skill.read_text(encoding="utf-8")
        if module.PYTHON_RESOLVER.as_posix() not in skill_text.replace("\\", "/"):
            raise AssertionError("Generated constitution skill does not reference the Python resolver")
        if module.declared_script_flavor(project, "codex") != "py":
            raise AssertionError("Spec Kit did not record the Python script flavor")
        flavor, referenced = module.inspect_script_runtime(project, "codex")
        if flavor != "py" or referenced != resolver:
            raise AssertionError("Preflight did not resolve the generated Python runtime")
        result = module.evaluate_preflight(
            "codex", project, environ={}, platform_name="nt"
        )
        if result != {"action": "continue", "script_flavor": "py"}:
            raise AssertionError(f"Usable Python resolver was unexpectedly rejected: {result}")

        integration_path = project / ".specify/integration.json"
        integration = json.loads(integration_path.read_text(encoding="utf-8"))
        integration["integration_settings"]["codex"]["script"] = "ps"
        integration_path.write_text(json.dumps(integration), encoding="utf-8")
        powershell_resolver = project / module.POWERSHELL_RESOLVER
        powershell_resolver.parent.mkdir(parents=True, exist_ok=True)
        powershell_resolver.write_text(
            "# Cross-platform fixture; execution is replaced by blocked_runner.\n",
            encoding="utf-8",
        )
        skill.write_text(
            skill_text.replace(
                module.PYTHON_RESOLVER.as_posix(),
                module.POWERSHELL_RESOLVER.as_posix(),
            ),
            encoding="utf-8",
        )

        def blocked_runner(*args, **kwargs):
            return subprocess.CompletedProcess(
                args=args[0],
                returncode=1,
                stdout="",
                stderr="PSSecurityException: the resolver is not digitally signed",
            )

        original_which = module.shutil.which
        module.shutil.which = lambda name: "powershell.exe" if name == "powershell" else None
        try:
            blocked = module.evaluate_preflight(
                "codex",
                project,
                environ={},
                platform_name="nt",
                runner=blocked_runner,
            )
        finally:
            module.shutil.which = original_which
        if blocked.get("action") != "script-runtime-blocked":
            raise AssertionError(f"Blocked PowerShell resolver was not rejected: {blocked}")
        require_phrases(
            "PowerShell resolver diagnostic",
            blocked["diagnostic"],
            (
                "PROGRAM_KIT_SPEC_KIT_SCRIPT_RUNTIME",
                "before intake or research",
                "PSSecurityException",
                "specify init . --force --non-interactive --integration codex --script py",
                ".specify/scripts/python/resolve_template.py",
                "Do not weaken",
            ),
        )
        reject_workaround("PowerShell resolver diagnostic", blocked["diagnostic"])


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
    validate_python_consumer(module)

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
    cases = boundary.get("cases", {})
    agent_blocked = cases.get("agent-boundary-blocked", [])
    runtime_blocked = cases.get("script-runtime-blocked", [])
    if len(agent_blocked) != 1 or len(runtime_blocked) != 1:
        raise AssertionError("Each Codex preflight failure must have one diagnostic step")
    error_command = agent_blocked[0].get("command", "")
    require_phrases(
        "Workflow-visible agent diagnostic",
        error_command,
        (
            "PROGRAM_KIT_CODEX_AGENT_BOUNDARY",
            "normal user-owned PowerShell or WSL terminal",
            "interactive Codex CLI agent",
            "Do not ask the agent",
            "rerunning init alone may not repair ownership",
        ),
    )
    runtime_command = runtime_blocked[0].get("command", "")
    require_phrases(
        "Workflow-visible runtime diagnostic",
        runtime_command,
        (
            "PROGRAM_KIT_SPEC_KIT_SCRIPT_RUNTIME",
            "before intake or research",
            ".agents/skills/speckit-constitution/SKILL.md",
            "--script py",
            ".specify/scripts/python/resolve_template.py",
            "Do not weaken execution policy",
        ),
    )
    reject_workaround("Workflow-visible agent diagnostic", error_command)
    reject_workaround("Workflow-visible runtime diagnostic", runtime_command)

    initializer = (root / "Initialize-ProgramKit.cmd").read_text(encoding="utf-8")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    require_phrases(
        "Consumer initializer",
        initializer,
        (
            "specify init . --force --non-interactive --integration codex --script py",
            f'set "PROGRAM_KIT_REF=v{version}"',
            "specify workflow add program-kit-bootstrap",
            "specify bundle install program-kit --integration codex",
            "No initial design was required",
            "INITIAL_DESIGN.md",
        ),
    )
    reject_workaround("Consumer initializer", initializer)

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
            "--script py",
            "resolve_template.py",
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
            "Initialize-ProgramKit.cmd",
            "--script py",
        ),
    )
    reject_workaround("Root Windows guide", root_guidance)

    print("Codex bootstrap boundary, Python resolver, and packaged guidance are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
