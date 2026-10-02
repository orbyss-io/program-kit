"""Invocation-scoped Codex write policy; never changes user config or trust.

The native Windows probe executes Python under Codex's sandbox, not a model.
Its success proves those artifact directories are writable in that probe; it
does not claim that a subsequent model turn completed its artifact contract.
"""
from __future__ import annotations

import contextlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

EXTRA_ARGS = 'SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS'
SAFE_VALUES = {'--model', '-m', '--profile', '-p', '--color'}
SAFE_SWITCHES = {'--json', '--ephemeral'}
SAFE_CONFIG = {'model', 'model_reasoning_effort', 'model_reasoning_summary', 'model_verbosity'}


class WorkerPolicyError(ValueError):
    pass


def diagnostic(problem: str) -> str:
    return f'''PROGRAM_KIT_CODEX_WORKSPACE_WRITE

Program Kit stopped before Codex worker dispatch: {problem}
Artifact-writing workers require explicit --sandbox workspace-write. Codex exec
defaults to read-only; project config and project trust do not establish this
dispatch contract. Full filesystem access is not required.

From a normal user-owned PowerShell terminal, use Program Kit's lifecycle entry
point (run for a new run, resume --run-id <id> for an existing stopped run):
  python .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id <id>

Do not change saved run state, move review gates, disable the sandbox, or grant
full filesystem access. If Codex rejects workspace-write or its native sandbox
probe fails, inspect Codex's configuration/requirements and the exact artifact
directory permissions. Ask the policy administrator if managed requirements
forbid workspace writes. Upgrade Codex if `codex sandbox` is unsupported.
Spec Kit's upstream adapter needs an explicit per-dispatch sandbox/write contract
instead of relying on codex exec defaults or a manual EXTRA_ARGS variable.
'''


def parse_extra(value: str, *, require_write: bool = False) -> list[str]:
    """Keep model/output options, reject competing permission or root overrides.

Spec Kit parses EXTRA_ARGS with POSIX shlex on Windows too. Use the same grammar
and serialize with shlex.join, so quoted profile/model names round-trip.
"""
    try:
        tokens = shlex.split(value)
    except ValueError as error:
        raise WorkerPolicyError(diagnostic('EXTRA_ARGS has invalid quoting')) from error
    result = []
    sandbox = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        key, separator, inline = token.partition('=')
        if key in {'--sandbox', '-s'} | SAFE_VALUES | {'-c', '--config'}:
            if separator:
                value = inline
            else:
                index += 1
                if index >= len(tokens):
                    raise WorkerPolicyError(diagnostic(f'{key} is missing its value'))
                value = tokens[index]
            if key in {'--sandbox', '-s'}:
                sandbox.append(value)
                if value != 'workspace-write':
                    raise WorkerPolicyError(diagnostic('EXTRA_ARGS requests a conflicting sandbox'))
            elif key in {'-c', '--config'}:
                setting = value.partition('=')[0].strip()
                if setting not in SAFE_CONFIG:
                    raise WorkerPolicyError(diagnostic('EXTRA_ARGS contains an unsupported config override; keep permission/root settings out of worker arguments'))
                result.extend([key, value])
            else:
                result.extend([key, value])
        elif token in SAFE_SWITCHES:
            result.append(token)
        else:
            # Fail closed for aliases, concatenated short flags, --add-dir,
            # --worktree, bypass flags and future permission-profile options.
            raise WorkerPolicyError(diagnostic('EXTRA_ARGS contains an unsupported option; only model, profile, output and workspace-write options are supported'))
        index += 1
    if require_write and sandbox != ['workspace-write']:
        raise WorkerPolicyError(diagnostic('the dispatch arguments do not select exactly one workspace-write sandbox; use the lifecycle entry point'))
    return result


def inspect_adapter():
    """Build argv through the installed adapter without dispatching a worker."""
    try:
        from specify_cli.integrations import get_integration
        integration = get_integration('codex')
        argv = integration.build_exec_args('Program Kit permission check', output_json=False)
    except (ImportError, AttributeError, TypeError, ValueError) as error:
        raise WorkerPolicyError(diagnostic('the installed Spec Kit Codex adapter cannot expose its dispatch argv; upgrade Spec Kit')) from error
    if not argv or len(argv) < 3 or argv[1] != 'exec':
        raise WorkerPolicyError(diagnostic('the installed Spec Kit Codex adapter has an unsupported dispatch contract'))
    parse_extra(shlex.join(argv[3:]), require_write=True)
    executable = shutil.which(argv[0])
    if not executable:
        raise WorkerPolicyError(diagnostic('the Codex executable selected by Spec Kit is unavailable'))
    argv[0] = executable
    return argv


def verify_windows_write(root: Path, argv: list[str], *, runner=subprocess.run) -> dict:
    """Use the selected executable and config profile for a model-free write test."""
    directories = [root, root / 'docs/architecture', root / '.specify/memory', root / '.specify/governance']
    created = []
    nonce = uuid.uuid4().hex
    targets = []
    try:
        for directory in directories:
            if not directory.exists():
                # Record every newly created ancestor; remove only empty ones.
                missing = []
                cursor = directory
                while not cursor.exists():
                    missing.append(cursor)
                    cursor = cursor.parent
                directory.mkdir(parents=True)
                created.extend(reversed(missing))
            targets.append(directory / f'.program-kit-write-probe-{nonce}')
        code = ('import pathlib,sys; '
                '[(pathlib.Path(p).write_text(sys.argv[1],encoding="utf-8")) for p in sys.argv[2:]]; '
                'assert all(pathlib.Path(p).read_text(encoding="utf-8")==sys.argv[1] for p in sys.argv[2:]); '
                '[pathlib.Path(p).unlink() for p in sys.argv[2:]]; '
                'print("PROGRAM_KIT_WRITE_PROBE_OK:"+sys.argv[1])')
        # Forward the profile and approved config options used by exec. This
        # native sandbox CLI requires a named profile; explicitly include
        # managed requirements so the control cannot sidestep device policy.
        options = parse_extra(shlex.join(argv[3:]), require_write=True)
        configuration = []
        index = 0
        while index < len(options):
            if options[index] in {'--profile', '-p', '-c', '--config'}:
                configuration.extend(options[index:index + 2])
                index += 2
            elif options[index] in SAFE_VALUES:
                index += 2
            else:
                index += 1
        # The isolated Specify interpreter may live in a user-private uv
        # directory that the Windows sandbox identity cannot execute. Probe the
        # PATH Python used by native workflow shell steps, not that supervisor.
        shell_python = shutil.which('python')
        if not shell_python:
            raise WorkerPolicyError(diagnostic('the workflow PATH Python is unavailable for the native write probe'))
        command = [argv[0], 'sandbox', '--permission-profile', ':workspace', '--include-managed-config', *configuration,
                   '--cd', str(root), '--', shell_python, '-I', '-c', code, nonce, *map(str, targets)]
        try:
            result = runner(command, cwd=root, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=60, check=False)
        except (OSError, subprocess.SubprocessError) as error:
            raise WorkerPolicyError(diagnostic('the native Codex sandbox write probe could not complete; no coding agent was started')) from error
        # A new sandbox-created file can have a DACL readable only by that
        # identity. Verify readback and delete inside the same native process,
        # then require its nonce-bound marker and no leftover files. This probe
        # proves sandbox writes, not supervisor readability of future artifacts.
        cleaned = all(not path.exists() for path in targets)
        marker = 'PROGRAM_KIT_WRITE_PROBE_OK:' + nonce
        if result.returncode or marker not in result.stdout.splitlines() or not cleaned:
            from compatibility_diagnostics import sanitize
            detail = sanitize((result.stderr or result.stdout or 'no sandbox diagnostic').strip())[-1600:]
            raise WorkerPolicyError(diagnostic(f'native sandbox write probe failed (exit {result.returncode}): {detail}'))
        return {'kind': 'native-sandbox-write-probe', 'codingAgentStarted': False,
                'directories': [path.relative_to(root).as_posix() for path in directories],
                'writesVerified': True, 'sandboxReadbackVerified': True, 'cleanupVerified': True,
                'supervisorArtifactReadability': 'not established by this sandbox write probe',
                'exitCode': result.returncode}
    finally:
        active_error = sys.exc_info()[1]
        cleanup_errors = []
        for path in targets:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                cleanup_errors.append(str(path))
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass  # Never remove worker/user content or recurse.
        if cleanup_errors:
            detail = 'Native probe cleanup could not remove its own files: ' + ', '.join(cleanup_errors)
            if active_error is not None:
                active_error.args = (str(active_error) + '\n' + detail,)
            else:
                raise WorkerPolicyError(diagnostic(detail))


@contextlib.contextmanager
def worker_environment(root: Path, requested: str, *, runner=subprocess.run):
    """Scope explicit least-privilege argv to this human-owned lifecycle call."""
    from codex_bootstrap_preflight import resolve_integration, is_codex_agent_invocation, diagnostic as boundary_diagnostic
    if resolve_integration(requested, root) != 'codex':
        yield
        return
    if is_codex_agent_invocation(integration='codex'):
        raise WorkerPolicyError(boundary_diagnostic())
    previous = os.environ.get(EXTRA_ARGS)
    options = parse_extra(previous or '')
    os.environ[EXTRA_ARGS] = shlex.join([*options, '--sandbox', 'workspace-write'])
    try:
        argv = inspect_adapter()
        # New append-only evidence per invocation; never rewrite historic runs.
        evidence = root / '.specify/workflows/worker-preflights' / (uuid.uuid4().hex + '.json')
        evidence.parent.mkdir(parents=True, exist_ok=True)
        record = {'schemaVersion': 1, 'projectRoot': str(root),
            'requestedSandbox': 'workspace-write', 'adapterArgv': argv,
            'workerEffectivePermissions': 'see worker session metadata'}
        try:
            record['probe'] = verify_windows_write(root, argv, runner=runner) if os.name == 'nt' else {
                'kind': 'argv-contract-only', 'codingAgentStarted': False, 'writesVerified': False}
        except (WorkerPolicyError, OSError) as error:
            from compatibility_diagnostics import sanitize
            record['status'] = 'blocked'
            record['diagnostic'] = sanitize(str(error))
            evidence.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
            detail = record['diagnostic'] if isinstance(error, WorkerPolicyError) else diagnostic(record['diagnostic'])
            raise WorkerPolicyError(f'{detail}\nPreserved preflight evidence: {evidence}') from error
        record['status'] = 'passed'
        evidence.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        print(f'Program Kit Codex worker preflight: workspace-write; evidence: {evidence}', file=sys.stderr)
        yield
    finally:
        if previous is None:
            os.environ.pop(EXTRA_ARGS, None)
        else:
            os.environ[EXTRA_ARGS] = previous
