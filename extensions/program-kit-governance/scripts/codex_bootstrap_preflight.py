from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Mapping


CODEX_AGENT_ENVIRONMENT_KEYS = (
    "CODEX_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_INTERNAL_ORIGINATOR_OVERRIDE",
)


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


def run_preflight(integration: str, project_root: Path) -> int:
    resolved = resolve_integration(integration, project_root)
    if not is_codex_agent_invocation(integration=resolved):
        return 0
    print(diagnostic(), file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stop Program Kit orchestration launched from a Codex agent."
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
    if args.json:
        resolved = resolve_integration(args.integration, project_root)
        blocked = is_codex_agent_invocation(integration=resolved)
        print(json.dumps({"action": "blocked" if blocked else "continue"}))
        return 0
    return run_preflight(args.integration, project_root)


if __name__ == "__main__":
    raise SystemExit(main())
