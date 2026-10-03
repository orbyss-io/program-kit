"""Verify shell runtime lookup before dispatch or workflow-history mutation."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess


class ShellPreflightError(ValueError):
    pass


def check_path(value: str, label: str) -> None:
    if os.name == 'nt' and len(value) > 8191:
        raise ShellPreflightError(
            f'WORKFLOW_SHELL_PREFLIGHT: {label} PATH is {len(value)} characters; '
            'Windows cmd.exe ignores inherited variables longer than 8191 characters. '
            'Use a bounded invocation-scoped PATH containing the installed workflow tools '
            '(including Python and any npm Codex launcher Node runtime), then retry the '
            'same lifecycle command. No worker was dispatched or workflow history changed. '
            'This is command lookup, not a workspace-write permission failure.')


def verify_shell_launch(root: Path, *, runner=subprocess.run) -> dict:
    """Check the inherited environment using the shell engine's execution mode.

    Absolute-path Python provisioning and a native sandbox write probe do not
    establish that bare `python` works through shell=True on Windows.
    No global environment or permissions are changed by this preflight.
    """
    inherited_path = os.environ.get('PATH', '')
    check_path(inherited_path, 'inherited')  # Before even the absolute dependency probe.
    from python_runtime import selected, invocation_values
    try:
        selected_python = selected(root)
        environment = invocation_values(selected_python)
    except (ValueError, OSError) as error:
        raise ShellPreflightError(f'WORKFLOW_SHELL_PREFLIGHT: cannot select the workflow Python: {error}') from error
    check_path(environment['PATH'], 'workflow')
    expected_python = shutil.which('python', path=environment['PATH'])
    if not expected_python:
        raise ShellPreflightError('WORKFLOW_SHELL_PREFLIGHT: python is unavailable on PATH; no worker was dispatched.')
    if not os.path.samefile(expected_python, selected_python):
        raise ShellPreflightError('WORKFLOW_SHELL_PREFLIGHT: bare python on the workflow PATH differs from '
                                 'the recorded interpreter; regenerate instructions with the intended Python.')
    # Fixed command: no repository paths, credentials or user text are interpolated.
    command = 'python -I -c "import json,sys;print(json.dumps({\'marker\':\'PROGRAMKIT_SHELL_OK\',\'python\':sys.executable}))"'
    try:
        # ShellStep also removes this engine-owned variable when no workflow_dir is set.
        environment.pop('SPECKIT_WORKFLOW_DIR', None)
        result = runner(command, shell=True, cwd=root, env=environment,
                        capture_output=True, encoding='utf-8', errors='replace',
                        timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        from compatibility_diagnostics import sanitize
        raise ShellPreflightError('WORKFLOW_SHELL_PREFLIGHT: workflow shell probe could not complete: '
                                 + sanitize(str(error))[-1600:] + '; no worker was dispatched.') from error
    try:
        observed = json.loads(result.stdout) if result.returncode == 0 else None
    except (json.JSONDecodeError, TypeError):
        observed = None
    matches = (isinstance(observed, dict)
               and observed.get('marker') == 'PROGRAMKIT_SHELL_OK'
               and isinstance(observed.get('python'), str)
               and os.path.normcase(os.path.abspath(observed['python']))
               == os.path.normcase(os.path.abspath(expected_python)))
    if not matches:
        from compatibility_diagnostics import sanitize
        detail = sanitize(result.stderr or result.stdout or 'no shell diagnostic')[-1600:]
        raise ShellPreflightError(
            f'WORKFLOW_SHELL_PREFLIGHT: bare python failed or resolved a different interpreter '
            f'through the workflow shell (exit {result.returncode}): {detail}. '
            'Correct the invocation environment before retrying; no worker was dispatched.')
    return {'kind': 'workflow-shell-launch', 'pathCharacters': len(environment['PATH']),
            'inheritedPathCharacters': len(inherited_path), 'selectedPython': selected_python,
            'python': observed['python'], 'codingAgentStarted': False, 'exitCode': 0}
