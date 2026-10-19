"""Real tracked-installation upgrade, source merge, activation and recovery; no agents."""
from pathlib import Path
from contextlib import ExitStack
import json
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch
import zipfile

from owned_fixture import FixtureDirectory, native_path
from local_bundle_fixture import install_local_bundle
import validate_consumer_upgrade_install as package

ROOT = package.ROOT
flow = package.flow


def main():
    version = (ROOT / 'VERSION').read_text().strip()
    previous = next(row['previous'] for row in flow.read(ROOT / 'releases/history.json')['entries']
                    if row['version'] == version)
    archive = ROOT / 'artifacts' / f'program-kit-{version}.zip'
    with FixtureDirectory() as name, ExitStack() as context:
        base = Path(name)
        scratch = base / 'tmp'
        scratch.mkdir()
        context.enter_context(patch.dict(os.environ, dict.fromkeys(('TEMP', 'TMP', 'TMPDIR'), native_path(scratch))))
        context.enter_context(patch.object(tempfile, 'tempdir', native_path(scratch)))
        old, release, source, target = (base / n for n in ('previous', 'candidate', 'consumer', 'upgrade'))
        history = base / 'previous.zip'
        subprocess.run(['git', 'archive', '--format=zip', '--output=' + native_path(history),
                        'v' + previous, 'VERSION', 'bundle.yml', 'extensions', 'presets', 'workflows'],
                       cwd=ROOT, capture_output=True, check=True, timeout=30)
        with zipfile.ZipFile(history) as z: z.extractall(old)
        with zipfile.ZipFile(archive) as z: z.extractall(release)
        source.mkdir()
        source, target, release = (Path(native_path(p)) for p in (source, target, release))
        flow.git(source, 'init')
        flow.git(source, 'config', '--local', 'core.autocrlf', 'false')
        flow.git(source, 'config', '--local', 'core.longpaths', 'true')
        (source / '.gitignore').write_text('artifacts/\n__pycache__/\n')
        import specify_cli
        bridge = [sys.executable, str(release / 'scripts/invoke_specify.py'), '--site-packages',
                  str(Path(specify_cli.__file__).parent.parent), '--']
        def run(command, root=source, expected_exit=0):
            return package.run([str(v) for v in command], root, expected_exit=expected_exit)
        run([*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
             '--script', 'py', '--ignore-agent-tools'])
        install_local_bundle(source, old, bridge, lambda label, argv: run(argv))
        # Capture actual final native generation after all preset layers exist.
        run([*bridge, 'integration', 'use', 'codex'])
        package.fixture_runtime(source)
        package.schema_runtime.record_copy(source)
        (source / 'note.txt').write_text('retained output\n')
        authority = '.specify/memory/consumer-intent.md'
        (source / authority).write_text('original intent\n')
        def commit(root, message):
            flow.git(root, 'add', '.')
            flow.git(root, '-c', 'user.name=Tracked Fixture', '-c', 'user.email=fixture@example.invalid',
                     'commit', '-m', message)
        commit(source, 'Real original installation and generated skills tracked')
        adapter = release / 'scripts/consumer_upgrade_workspace.py'
        def workspace(command, root=target, *extra, expected_exit=0):
            return run([sys.executable, adapter, command, '--target', target,
                        *extra], root, expected_exit)
        run([sys.executable, adapter, 'prepare', '--source', source, '--target', target,
             '--release-root', release, '--branch', 'tracked-upgrade'])
        package.fixture_runtime(target)
        # Reconcile fictional consumer intent before installation captures its
        # exact input set. Editing it afterward must invalidate readiness.
        (target / authority).write_text('reviewed retained intent\n')
        installed = json.loads(workspace('install', target, '--release-root', release, '--offline'))
        if installed['updaterExitCode'] != 0:
            logs = '\n'.join((target / p).read_text(encoding='utf-8') for p in installed['updaterEvidence'])
            (package.RUN / 'isolated-updater-failure.log').write_text(logs, encoding='utf-8')
            raise AssertionError(logs)
        checks = [{'id': 'retained-output', 'command': [sys.executable, '-c',
                   "from pathlib import Path; assert Path('note.txt').read_text() == 'retained output\\n'; "
                   "assert Path('.specify/memory/consumer-intent.md').read_text() == 'reviewed retained intent\\n'"]}]
        flow.atomic(target / 'artifacts/checks.json', checks)
        cli = target / '.specify/extensions/program-kit-governance/scripts/consumer_upgrade.py'
        run([sys.executable, cli, 'assess'], target)
        run([sys.executable, cli, 'verify', '--input', 'artifacts/checks.json'], target)
        workspace('integrate', target, '--destination', source)
        commit(target, 'Reviewed candidate installed tree and generated skills')
        # Ordinary source integration carries the tracked installation and real
        # generation records together; no byte projection is performed by the test.
        flow.git(source, 'merge', '--ff-only', flow.git(target, 'rev-parse', 'HEAD'))
        tracked = flow.git(source, 'ls-files').splitlines()
        assert any(p.startswith('.specify/extensions/') for p in tracked)
        assert any(p.startswith('.agents/skills/') for p in tracked)
        before = flow.installation_inputs(source)
        original = flow.read(source / flow.RECORD)['sourceVersion']
        assert original == previous
        # Reject an unreviewed installation edit before mutation.
        changed = source / '.specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.architecture.md'
        pristine = changed.read_bytes()
        changed.write_bytes(pristine + b'\nUnreviewed concurrent edit\n')
        flow.atomic(source / 'artifacts/checks.json', checks)
        workspace('activate', source, '--destination', source, '--release-root', release,
                  '--input', 'artifacts/checks.json', '--offline', expected_exit=2)
        assert changed.read_bytes() == pristine + b'\nUnreviewed concurrent edit\n'
        changed.write_bytes(pristine)  # Explicit restoration of this fictional edit.
        assert flow.installation_inputs(source) == before
        flow.atomic(source / 'artifacts/checks.json', [{'id': 'real-outcome-loss',
                    'command': [sys.executable, '-c', 'raise SystemExit(9)']}])
        workspace('activate', source, '--destination', source, '--release-root', release,
                  '--input', 'artifacts/checks.json', '--offline', expected_exit=2)
        ledgers = list((source / 'artifacts/program-kit/consumer-activation').glob('*/activation.json'))
        assert len(ledgers) == 1 and flow.read(ledgers[0])['status'] == 'recovered'
        assert flow.read(ledgers[0])['diagnostic'].startswith(
            'PKU140 Destination installation or affected readiness did not converge'), flow.read(ledgers[0])['diagnostic']
        assert flow.installation_inputs(source) == before, 'Recovery must restore exact pre-activation merged bytes'
        flow.atomic(source / 'artifacts/checks.json', checks)
        activated = json.loads(workspace('activate', source, '--destination', source, '--release-root', release,
                                        '--input', 'artifacts/checks.json', '--offline'))
        assert activated['activated'] and not activated['applicationAcceptanceEstablished']
        assert flow.inputs(source) == flow.inputs(target)
        assert flow.load(source)['checks'][0]['executionRoot'] == str(source)
        flow.atomic(package.RUN / 'tracked-summary.json', {'fromVersion': previous, 'toVersion': version,
                    'trackedInstallationActivated': True, 'failedOutcomeRecovered': True,
                    'unreviewedEditPreserved': True, 'codingAgentsStarted': False})
    print('Tracked installed source, actual native generation, source integration and destination activation passed.')


if __name__ == '__main__':
    main()
