"""Actual PowerShell/child-process checks with synthetic provider values only."""
import json
import os
from pathlib import Path
import subprocess
import sys


def exercise(shell, repository, wrapper, environment):
    eng = repository / 'eng'
    config = eng / 'verification.json'
    config.write_text(json.dumps({'schemaVersion': 1, 'testGroups': [], 'providerIsolation': {'required': True}}))
    marker = repository / 'isolation-child.marker'
    consumer = eng / 'verify.ps1'
    consumer.write_text("Set-Content -LiteralPath $env:PROGRAMKIT_ISOLATION_MARKER -Value 'dispatched'\n")
    env = dict(environment, PROGRAMKIT_ISOLATION_MARKER=str(marker), PROGRAMKIT_TEST_PYTHON=sys.executable)
    command = [shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(wrapper)]
    missing = subprocess.run(command, env=env, capture_output=True, text=True)
    if marker.exists() or missing.returncode == 0 or 'PKV004' not in missing.stdout + missing.stderr:
        raise AssertionError('Missing required isolation dispatched a verification child')
    module = eng / 'ProviderTestEnvironment.psm1'
    module.write_text("function Unrelated {}\nExport-ModuleMember -Function Unrelated\n")
    invalid = subprocess.run(command, env=env, capture_output=True, text=True)
    if marker.exists() or invalid.returncode == 0 or 'PKV004' not in invalid.stdout + invalid.stderr:
        raise AssertionError('Invalid isolation module dispatched a verification child')
    module.write_text('''function Invoke-WithOfflineProviderTestEnvironment {
param([scriptblock]$Action)
$oldKey = $env:PROGRAMKIT_SYNTHETIC_PROVIDER_KEY
$oldMode = $env:PROGRAMKIT_SYNTHETIC_PROVIDER_MODE
try {
    $env:PROGRAMKIT_SYNTHETIC_PROVIDER_KEY = $null
    $env:PROGRAMKIT_SYNTHETIC_PROVIDER_MODE = 'offline'
    & $Action
} finally {
    $env:PROGRAMKIT_SYNTHETIC_PROVIDER_KEY = $oldKey
    $env:PROGRAMKIT_SYNTHETIC_PROVIDER_MODE = $oldMode
}
}
Export-ModuleMember -Function Invoke-WithOfflineProviderTestEnvironment
''')
    child = repository / 'check_environment.py'
    child.write_text("import os,pathlib,sys\nassert not os.environ.get('PROGRAMKIT_SYNTHETIC_PROVIDER_KEY')\n"
                     "assert os.environ.get('PROGRAMKIT_SYNTHETIC_PROVIDER_MODE')=='offline'\n"
                     "pathlib.Path(os.environ['PROGRAMKIT_ISOLATION_MARKER']).write_text('isolated')\n"
                     "sys.exit(7 if os.environ.get('PROGRAMKIT_ISOLATION_FAIL') else 0)\n")
    consumer.write_text("& $env:PROGRAMKIT_TEST_PYTHON (Join-Path $PSScriptRoot '../check_environment.py')\n"
                        "if ($LASTEXITCODE) { throw 'Child isolation failed' }\n"
                        "if ($env:PROGRAMKIT_ISOLATION_FAIL) { throw 'Synthetic verification failure' }\n")
    launcher = repository / 'check_parent.ps1'
    launcher.write_text('''$ErrorActionPreference='Stop'
$env:PROGRAMKIT_SYNTHETIC_PROVIDER_KEY='synthetic-parent-value'
$env:PROGRAMKIT_SYNTHETIC_PROVIDER_MODE='live-synthetic'
$failed=$false
$extra=@{}
if ($env:PROGRAMKIT_ISOLATION_SCOPE) { $extra.Scope='Focused'; $extra.Projects=@('tests/Synthetic.Tests.csproj') }
try { & (Join-Path $PSScriptRoot 'eng/Invoke-RepositoryVerification.ps1') @extra } catch { $failed=$true }
if ($env:PROGRAMKIT_SYNTHETIC_PROVIDER_KEY -ne 'synthetic-parent-value' -or
    $env:PROGRAMKIT_SYNTHETIC_PROVIDER_MODE -ne 'live-synthetic') { throw 'Parent environment was not restored' }
if ($failed -ne [bool]$env:PROGRAMKIT_ISOLATION_FAIL) { throw 'Wrong verification outcome' }
''')
    build = eng / 'Build.ps1'
    original_build = build.read_bytes()
    build.write_text("param([switch]$SkipReleaseBundle,[switch]$LockedMode,[switch]$VerifyArchitecture)\n"
                     "& $env:PROGRAMKIT_TEST_PYTHON (Join-Path $PSScriptRoot '../check_environment.py')\n"
                     "if ($LASTEXITCODE) { throw 'Synthetic fallback failure' }\n")
    native = eng / 'repository_verification.py'
    native.write_bytes(child.read_bytes())
    adapter = eng / 'verify-scoped.ps1'
    consumer_text = consumer.read_text()
    for route in ('consumer', 'fallback', 'scoped-native', 'scoped-adapter'):
        if route == 'fallback':
            consumer.unlink()
        if route == 'scoped-adapter':
            adapter.write_text('param($Scope,$Projects,$TestArguments,$ChangedPaths,$ChangedFrom,$FeatureDirectory,$Configuration,[switch]$Restore,[switch]$Plan)\n' + consumer_text)
        for failed in (False, True):
            marker.unlink(missing_ok=True)
            case_env = dict(env)
            case_env.pop('PROGRAMKIT_TEST_EXIT', None)
            if route.startswith('scoped'):
                case_env['PROGRAMKIT_ISOLATION_SCOPE'] = '1'
            if failed:
                case_env['PROGRAMKIT_ISOLATION_FAIL'] = '1'
            result = subprocess.run([shell, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(launcher)],
                                    env=case_env, capture_output=True, text=True)
            if result.returncode or not marker.exists() or marker.read_text() != 'isolated':
                raise AssertionError('Isolation/parent restoration failed for ' + route + ': ' + result.stdout + result.stderr)
    adapter.unlink()
    native.unlink()
    build.write_bytes(original_build)
    module.unlink()
    config.write_text(json.dumps({'schemaVersion': 1, 'testGroups': []}))
    consumer.write_text("Set-Content -LiteralPath $env:PROGRAMKIT_ISOLATION_MARKER -Value 'plain'\n")
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode or marker.read_text().strip() != 'plain':
        raise AssertionError('Repository without provider integration failed: ' + result.stdout + result.stderr)
    runtime = repository / '.specify/python-runtime.json'
    original = runtime.read_bytes()
    for record in ({'contractVersion': 1, 'executable': str(repository / 'missing-python.exe')},
                   {'contractVersion': 999, 'executable': sys.executable}):
        runtime.write_text(json.dumps(record))
        marker.unlink(missing_ok=True)
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        if result.returncode == 0 or marker.exists() or 'PKV005' not in result.stdout + result.stderr:
            raise AssertionError('Invalid/stale Python did not fail before verification dispatch')
    runtime.write_bytes(original)
    (repository / '.python-version').write_text('0.0.0')
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode == 0 or marker.exists() or 'PKV005' not in result.stdout + result.stderr:
        raise AssertionError('Interpreter version mismatch was accepted')
    (repository / '.python-version').unlink()
    config.unlink()
    consumer.unlink()
    print('Required isolation admission, real child clearing/offline, parent restoration and Python diagnostics passed.')
