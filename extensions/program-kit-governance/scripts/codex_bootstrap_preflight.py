from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping


CODEX_AGENT_ENVIRONMENT_KEYS = (
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
)
CONSTITUTION_SKILL = Path(".agents/skills/speckit-constitution/SKILL.md")
PYTHON_RESOLVER = Path(".specify/scripts/python/resolve_template.py")
POWERSHELL_RESOLVER = Path(".specify/scripts/powershell/resolve-template.ps1")
SHELL_RESOLVER = Path(".specify/scripts/bash/resolve-template.sh")
SUPPORTED_RESOLVERS = {
    "py": PYTHON_RESOLVER,
    "ps": POWERSHELL_RESOLVER,
    "sh": SHELL_RESOLVER,
}


def resolve_integration(requested: str, project_root: Path) -> str:
    """Resolve Spec Kit's ``auto`` integration without importing Spec Kit."""
    value = requested.strip().lower()
    if value and value != "auto":
        return value

    candidates = (
        (project_root / ".specify" / "integration.json", ("default_integration", "integration")),
        (project_root / ".specify" / "init-options.json", ("integration", "ai")),
    )
    for path, keys in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        for key in keys:
            candidate = payload.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip().lower()
    return value


def is_codex_agent_invocation(
    *,
    integration: str,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Detect an outer Program Kit run launched by a Codex agent session."""
    if integration.lower() != "codex":
        return False
    environ = environ if environ is not None else os.environ
    return any(environ.get(key) for key in CODEX_AGENT_ENVIRONMENT_KEYS)


def _read_json_object(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def declared_script_flavor(project_root: Path, integration: str) -> str:
    """Read the script flavor recorded by Spec Kit initialization."""
    integration_state = _read_json_object(project_root / ".specify" / "integration.json")
    settings = integration_state.get("integration_settings")
    if isinstance(settings, dict):
        selected = settings.get(integration)
        if isinstance(selected, dict):
            value = selected.get("script")
            if isinstance(value, str) and value.strip():
                return value.strip().lower()

    init_options = _read_json_object(project_root / ".specify" / "init-options.json")
    value = init_options.get("script")
    return value.strip().lower() if isinstance(value, str) else ""


def referenced_constitution_resolver(project_root: Path) -> tuple[str, Path]:
    """Resolve the executable template resolver named by the installed constitution skill."""
    skill = project_root / CONSTITUTION_SKILL
    try:
        text = skill.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Installed constitution skill is missing or unreadable: {skill}") from exc

    normalized = text.replace("\\", "/")
    matches = [
        (flavor, resolver)
        for flavor, resolver in SUPPORTED_RESOLVERS.items()
        if resolver.as_posix() in normalized
    ]
    if len(matches) != 1:
        references = sorted(
            set(re.findall(r"\.specify/scripts/[^\s`]+resolve[^\s`]+", normalized))
        )
        detail = ", ".join(references) if references else "none"
        raise RuntimeError(
            "Installed constitution skill does not name exactly one supported resolver "
            f"(found: {detail})"
        )
    return matches[0]


def inspect_script_runtime(project_root: Path, integration: str) -> tuple[str, Path]:
    """Inspect and cross-check Spec Kit's recorded and generated script flavors."""
    referenced_flavor, relative_resolver = referenced_constitution_resolver(project_root)
    declared_flavor = declared_script_flavor(project_root, integration)
    if declared_flavor and declared_flavor != referenced_flavor:
        raise RuntimeError(
            "Spec Kit script flavor is inconsistent: initialization records "
            f"{declared_flavor!r}, but the constitution skill references {referenced_flavor!r}"
        )
    resolver = project_root / relative_resolver
    if not resolver.is_file():
        raise RuntimeError(
            f"The constitution skill references a resolver that does not exist: {relative_resolver}"
        )
    return referenced_flavor, resolver


def _resolver_command(flavor: str, resolver: Path) -> list[str]:
    if flavor == "py":
        return [sys.executable, str(resolver), "constitution-template", "--json"]
    if flavor == "sh":
        executable = shutil.which("bash")
        if executable is None:
            raise RuntimeError("No Bash executable is available for the referenced resolver")
        return [executable, str(resolver), "constitution-template", "--json"]
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        raise RuntimeError("No PowerShell executable is available for the referenced resolver")
    return [
        executable,
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(resolver),
        "constitution-template",
        "-Json",
    ]


def verify_windows_resolver(
    project_root: Path,
    flavor: str,
    resolver: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """Execute the installed resolver exactly far enough to prove it is usable."""
    command = _resolver_command(flavor, resolver)
    child_environment = os.environ.copy()
    if flavor == "py":
        child_environment["PYTHONIOENCODING"] = "utf-8"
        child_environment["PYTHONUTF8"] = "1"
    try:
        result = runner(
            command,
            cwd=project_root,
            env=child_environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Resolver execution could not start: {exc}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "no diagnostic output").strip()
        detail = " ".join(detail.split())[:600]
        raise RuntimeError(f"Resolver execution failed with exit code {result.returncode}: {detail}")
    if "TEMPLATE_CONTENT" not in (result.stdout or ""):
        raise RuntimeError("Resolver execution did not return the expected template payload")


def diagnostic() -> str:
    return """PROGRAM_KIT_CODEX_AGENT_BOUNDARY

Program Kit stopped before Spec Kit started a nested Codex CLI.

The outer bootstrap command is running from a Codex Desktop task or an
interactive Codex CLI agent. Both are agent environments. Spec Kit dispatches
Codex workflow steps with `codex exec`, so the outer orchestration must instead
be started by the human from a normal user-owned shell.

On native Windows, Codex's preferred elevated sandbox uses dedicated
lower-privilege identities and filesystem permission boundaries. Running
initialization or installation from that identity can leave `.agents`,
`.specify`, or related paths owned by the sandbox identity. Later sandbox setup
may then fail while applying protective ACLs. Nested `codex exec` is a second,
independent reason not to start the outer workflow from an agent.

Open a normal PowerShell or WSL terminal yourself, change to the repository
root, and run the full command there, for example:

  specify workflow run program-kit-bootstrap --input initial_design=./INITIAL_DESIGN.md --input integration=codex

Do not ask this agent to run that command outside its sandbox, approve an
escalation exception, install an approval rule, or start another interactive
`codex` agent. The Spec Kit workers launched by the normal shell remain
sandboxed.

If an agent already performed initialization or installation, rerunning init
alone may not repair ownership. Review the clean-start and ownership guidance:
  .specify/extensions/program-kit-governance/references/codex-desktop-windows.md
"""


def script_runtime_diagnostic(problem: str) -> str:
    return f"""PROGRAM_KIT_SPEC_KIT_SCRIPT_RUNTIME

Program Kit stopped before intake or research because the installed Codex
constitution skill does not have a usable Spec Kit template resolver on
Windows.

{problem}

From a normal user-owned PowerShell terminal in the repository root, cleanly
regenerate Spec Kit's integration files with the Python flavor:

  specify init . --force --non-interactive --integration codex --script py

Then confirm that `.specify/scripts/python/resolve_template.py` exists and that
`.agents/skills/speckit-constitution/SKILL.md` references it before restarting
the Program Kit workflow. This merge-style reinitialization preserves installed
Program Kit extension registration, but review `git status` before continuing.

Do not weaken the machine or user execution policy, broadly unblock repository
files, or grant unrestricted execution. If ownership is already wrong, follow
the conservative clean-start guidance instead:
  .specify/extensions/program-kit-governance/references/codex-desktop-windows.md
"""


def evaluate_preflight(
    integration: str,
    project_root: Path,
    *,
    environ: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, str]:
    resolved = resolve_integration(integration, project_root)
    if is_codex_agent_invocation(integration=resolved, environ=environ):
        return {"action": "agent-boundary-blocked", "diagnostic": diagnostic()}
    if resolved != "codex":
        return {"action": "continue", "script_flavor": "not-applicable"}

    try:
        flavor, resolver = inspect_script_runtime(project_root, resolved)
        current_platform = platform_name if platform_name is not None else os.name
        if current_platform == "nt":
            verify_windows_resolver(project_root, flavor, resolver, runner=runner)
    except RuntimeError as exc:
        return {
            "action": "script-runtime-blocked",
            "diagnostic": script_runtime_diagnostic(str(exc)),
        }
    return {"action": "continue", "script_flavor": flavor}


def run_preflight(integration: str, project_root: Path) -> int:
    result = evaluate_preflight(integration, project_root)
    if result["action"] == "continue":
        return 0
    print(result["diagnostic"], file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Codex execution boundary and installed Spec Kit resolver."
    )
    parser.add_argument("--integration", default="auto")
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a workflow-switch action and always return success.",
    )
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    result = evaluate_preflight(args.integration, project_root)
    if args.json:
        print(json.dumps(result))
        return 0
    if result["action"] != "continue":
        print(result["diagnostic"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
