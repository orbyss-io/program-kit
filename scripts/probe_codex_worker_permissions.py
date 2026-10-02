"""Human-owned native Windows reproduction: fresh repository, no model sessions.

Captures real adapter argv and native sandbox write behavior. It does not run a
bootstrap workflow or claim a new codex exec session was reproduced.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import codex_bootstrap_preflight as preflight
import codex_worker_policy as policy
from compatibility_diagnostics import sanitize


def main():
    if os.name != 'nt' or any(os.environ.get(key) for key in preflight.CODEX_AGENT_ENVIRONMENT_KEYS):
        raise RuntimeError('Run this probe in a normal user-owned native Windows PowerShell terminal')
    try:
        from specify_cli.integrations import get_integration
    except ImportError:
        from workflow_lifecycle import installed_interpreter
        return subprocess.run([str(installed_interpreter()), str(Path(__file__).resolve())], check=False).returncode
    project = Path(tempfile.mkdtemp(prefix='program-kit-worker-permissions-')).resolve()
    evidence = ROOT / 'artifacts/codex-worker-permissions' / project.name
    evidence.mkdir(parents=True)
    print(f'Fresh repository: {project}\nPreserved evidence: {evidence}', flush=True)
    report = {'schemaVersion': 1, 'project': str(project), 'codingAgentStarted': False,
              'scope': 'adapter argv and native sandbox controls; no new exec session or bootstrap', 'commands': []}

    def run(command, label, **kwargs):
        result = subprocess.run(command, cwd=project, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=90, check=False, **kwargs)
        report['commands'].append({'label': label, 'argv': command, 'exitCode': result.returncode})
        (evidence / (label + '.stdout.log')).write_text(sanitize(result.stdout), encoding='utf-8')
        (evidence / (label + '.stderr.log')).write_text(sanitize(result.stderr), encoding='utf-8')
        (evidence / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return result

    try:
        for command, label in ((['git', 'init'], 'git-init'),
                               (['specify', 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
                                 '--script', 'py', '--ignore-agent-tools'], 'specify-init')):
            result = run(command, label)
            if result.returncode:
                raise RuntimeError(f'{label} failed; inspect preserved logs')
        codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
        config_path = codex_home / 'config.toml'
        config = tomllib.loads(config_path.read_text(encoding='utf-8')) if config_path.is_file() else {}
        project_settings = {key: value.get('trust_level') for key, value in config.get('projects', {}).items()
                            if os.path.normcase(key) == os.path.normcase(str(project))}
        report['config'] = {'userConfigPath': str(config_path), 'userSandboxMode': config.get('sandbox_mode'),
                            'selectedProfile': config.get('profile'), 'windowsSandbox': config.get('windows', {}).get('sandbox'),
                            'projectConfigExists': (project / '.codex/config.toml').is_file(),
                            'projectTrustEntries': project_settings,
                            'managedRequirements': 'see redacted codex-doctor output; not inferred from permission_profile.type'}
        previous = os.environ.pop(policy.EXTRA_ARGS, None)
        try:
            baseline = get_integration('codex').build_exec_args('Write fixture artifact', output_json=False)
            report['baselineAdapterArgv'] = baseline
            import shutil
            executable = shutil.which(baseline[0])
            shell_python = shutil.which('python')
            if not executable:
                raise RuntimeError('The adapter-selected Codex executable is unavailable')
            if not shell_python:
                raise RuntimeError('The workflow PATH Python is unavailable')
            run([executable, '--version'], 'codex-version')
            run([executable, 'doctor', '--json'], 'codex-doctor')
            target = project / 'read-only-control.txt'
            code = 'import pathlib,sys; pathlib.Path(sys.argv[1]).write_text("fixture",encoding="utf-8")'
            result = run([executable, 'sandbox', '--permission-profile', ':read-only', '--include-managed-config', '--cd', str(project), '--',
                          shell_python, '-I', '-c', code, str(target)], 'read-only-control')
            report['readOnlyControl'] = {'exitCode': result.returncode, 'fileCreated': target.exists()}
            if result.returncode == 0 or target.exists() or 'PermissionError' not in result.stderr:
                raise RuntimeError('Read-only control did not deny a write; inspect effective managed/config permissions')
            def probe_runner(command, **kwargs):
                # The policy helper supplies its own fixed runner contract.
                return run(command, 'workspace-write-control')
            with policy.worker_environment(project, 'codex', runner=probe_runner):
                report['correctedAdapterArgv'] = policy.inspect_adapter()
            report['preflights'] = [json.loads(path.read_text()) for path in
                                   (project / '.specify/workflows/worker-preflights').glob('*.json')]
            report['status'] = 'passed'
        finally:
            if previous is not None:
                os.environ[policy.EXTRA_ARGS] = previous
        print('Read-only denied writes; workspace-write wrote and cleaned all artifact probes. No coding agent or workflow started.')
        return 0
    except Exception as error:
        report['status'] = 'failed'
        report['diagnostic'] = sanitize(str(error))
        print(report['diagnostic'], file=sys.stderr)
        return 1
    finally:
        (evidence / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        # Preserve the disposable repository and all evidence for inspection.


if __name__ == '__main__':
    raise SystemExit(main())
