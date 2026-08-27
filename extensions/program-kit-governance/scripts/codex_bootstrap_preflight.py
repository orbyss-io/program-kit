from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
from pathlib import Path
from typing import Mapping


BOOTSTRAP_PREFIX = ("specify", "workflow", "run", "program-kit-bootstrap")
CODEX_SANDBOX_USER_PREFIX = "codexsandbox"


def matches_bootstrap_prefix(argv: list[str] | tuple[str, ...]) -> bool:
    """Return whether argv is covered by Program Kit's narrow Codex rule."""
    return tuple(argv[: len(BOOTSTRAP_PREFIX)]) == BOOTSTRAP_PREFIX


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


def current_windows_user() -> str:
    """Read the process-token user, not the outer user's inherited env vars."""
    if os.name != "nt":
        return ""
    size = ctypes.c_ulong(0)
    ctypes.windll.advapi32.GetUserNameW(None, ctypes.byref(size))
    if size.value == 0:
        return ""
    buffer = ctypes.create_unicode_buffer(size.value)
    if not ctypes.windll.advapi32.GetUserNameW(buffer, ctypes.byref(size)):
        return ""
    return buffer.value


def is_nested_codex_sandbox_unavailable(
    *,
    integration: str,
    platform_name: str | None = None,
    current_user: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Detect Codex dispatch from the native Windows elevated sandbox."""
    platform_name = platform_name if platform_name is not None else os.name
    if platform_name != "nt" or integration.lower() != "codex":
        return False

    current_user = current_user if current_user is not None else current_windows_user()
    environ = environ if environ is not None else os.environ
    is_sandbox_user = current_user.casefold().startswith(CODEX_SANDBOX_USER_PREFIX)
    is_codex_task = bool(
        environ.get("CODEX_SESSION_ID")
        or environ.get("CODEX_THREAD_ID")
        or environ.get("CODEX_INTERNAL_ORIGINATOR_OVERRIDE")
    )
    return is_sandbox_user and is_codex_task


def diagnostic() -> str:
    return """PROGRAM_KIT_CODEX_NESTED_SANDBOX

Program Kit stopped before Spec Kit started a nested Codex CLI.

Spec Kit 1.0.1 dispatches Codex workflow command steps with `codex exec`. This
command is currently running inside Codex Desktop's native Windows elevated
sandbox. The nested Codex process cannot resolve or write its protected Codex
home/state or initialize its app-server client there. CODEX_HOME, --ephemeral,
or a workspace SQLite directory do not make nested execution supported.

Keep the elevated sandbox enabled. From the current Codex task, rerun the outer
command outside the sandbox and approve only this exact prefix:

  specify workflow run program-kit-bootstrap

The full command may append Program Kit inputs such as:

  --input initial_design=./INITIAL_DESIGN.md --input integration=codex

You may choose Always allow only for the exact four-token prefix above. Do not
allow `specify workflow`, arbitrary workflow IDs, or arbitrary shell commands.
`specify workflow resume` is intentionally not covered and remains subject to
human approval at the assessment, constitution, and bootstrap gates.

PowerShell fallback: open an ordinary PowerShell terminal in this repository
and run the same full `specify workflow run program-kit-bootstrap ...` command.

Do not make %USERPROFILE%\\.codex writable to the sandbox, copy Codex state or
authentication into the project, enable danger-full-access globally, or weaken
the Windows sandbox. See:
  .specify/extensions/program-kit-governance/references/codex-desktop-windows.md
"""


def run_preflight(integration: str, project_root: Path) -> int:
    resolved = resolve_integration(integration, project_root)
    if not is_nested_codex_sandbox_unavailable(integration=resolved):
        return 0
    print(diagnostic(), file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect unsupported nested Codex execution before Program Kit bootstrap."
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
        blocked = is_nested_codex_sandbox_unavailable(integration=resolved)
        print(json.dumps({"action": "blocked" if blocked else "continue"}))
        return 0
    return run_preflight(args.integration, project_root)


if __name__ == "__main__":
    raise SystemExit(main())
