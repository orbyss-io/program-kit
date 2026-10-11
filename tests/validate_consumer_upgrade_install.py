"""Real packaged Specify/updater preparation and destination activation; no agents."""
from __future__ import annotations
import json
import argparse
import os
import shutil
import subprocess
import sys
import uuid
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'artifacts/consumer-upgrade-package-runs'/uuid.uuid4().hex
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'extensions/program-kit-governance/scripts')]
import consumer_upgrade as flow
import schema_runtime


def run(command, root, environment=None, expected_exit=0):
    result = subprocess.run(command, cwd=root, env={**os.environ, 'SPECIFY_INIT_DIR': str(root), 'PYTHONUTF8': '1', **(environment or {})},
                            capture_output=True, text=True, encoding='utf-8', timeout=600)
    RUN.mkdir(parents=True, exist_ok=True)
    attempt = str(len(list(RUN.glob('*.json'))))
    (RUN/(attempt+'-stdout.log')).write_text(result.stdout, encoding='utf-8')
    (RUN/(attempt+'-stderr.log')).write_text(result.stderr, encoding='utf-8')
    flow.atomic(RUN/(attempt+'.json'), {'command': command, 'exitCode': result.returncode})
    if result.returncode:
        evidence = RUN/(attempt+'-local-state')
        evidence.mkdir()
        for relative in ('.program-kit/consumer-upgrade.json', '.program-kit/installation/migration.json'):
            original = root/relative
            if original.is_file(): shutil.copy2(original, evidence/original.name)
        for directory in ('artifacts/program-kit/consumer-upgrade', 'artifacts/program-kit/consumer-activation'):
            if (root/directory).is_dir(): shutil.copytree(root/directory, evidence/Path(directory).name)
        record_path = root / flow.RECORD
        if record_path.is_file():
            isolated = Path(flow.read(record_path).get('workspace', {}).get('target', str(root)))
            if (isolated / flow.RECORD).is_file():
                flow.atomic(evidence/'isolated-status.json', flow.readiness(isolated))
        if result.returncode != expected_exit:
            raise AssertionError(f'{command}: {result.stdout}\n{result.stderr}')
    elif expected_exit:
        raise AssertionError('Expected failed activation unexpectedly passed')
    return result.stdout


def fixture_runtime(target):
    # Explicit fixture setup using the maintained, exact pinned runtime prepared for tests.
    # The production baseline adapter excludes this cache and never transports its readiness.
    source = schema_runtime.runtime_path(ROOT)
    if not (source/'.ready').is_file(): raise AssertionError('Prepare the maintained schema runtime before this package check')
    destination = schema_runtime.runtime_path(target)
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)


def check_installed_workflow(target):
    from validate_task_generation import validate_installed_workflow
    # The real drafting exercise selects a disposable feature. Restore that
    # selection afterward so this test does not invalidate captured installation
    # inputs while it checks upgrade readiness and activation recovery.
    selection = target/'.specify/feature.json'
    prior = selection.read_bytes() if selection.is_file() else None
    try:
        validate_installed_workflow(target)
    finally:
        if prior is None:
            selection.unlink(missing_ok=True)
        else:
            selection.write_bytes(prior)


def main():
    version = (ROOT/'VERSION').read_text().strip()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=ROOT/'artifacts'/f'program-kit-{version}.zip')
    archive = parser.parse_args().archive.resolve()
    with tempfile.TemporaryDirectory(prefix='consumer-upgrade-package-') as name:
        base = Path(name).resolve()
        release, source, target = base/'release', base/'consumer', base/'upgrade'
        with zipfile.ZipFile(archive) as package: package.extractall(release)
        source.mkdir()
        flow.git(source, 'init')
        run(['specify', 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'], source)
        from specify_cli._assets import get_speckit_version
        from specify_cli.bundles.adapters import DefaultPrimitiveInstaller
        from specify_cli.bundles.installer import install_bundle
        from specify_cli.bundles.manifest import BundleManifest
        from specify_cli.bundles.resolver import resolve_install_plan
        manifest = BundleManifest.from_file(release/'bundle.yml')
        native_plan = resolve_install_plan(manifest, speckit_version=get_speckit_version(), active_integration='codex')
        class LocalFixtureInstaller(DefaultPrimitiveInstaller):
            def install(self, root, component):
                arguments = {
                    'extensions': ['extension', 'add', str(release/'extensions'/component.id), '--dev'],
                    'workflows': ['workflow', 'add', str(release/'workflows'/component.id), '--dev'],
                    'presets': ['preset', 'add', '--dev', str(release/'presets'/component.id)],
                }[component.kind]
                run(['specify', *arguments], root)
        # Native core owns first-install pin/conflict/ownership records; no fabricated
        # bundle history and no public catalog lookup for these verified local fixtures.
        install_bundle(source, native_plan, LocalFixtureInstaller(allow_network=False), manifest=manifest)
        run([sys.executable, str(release/'scripts/record_local_bundle.py'), '--release-root', str(release), '--target', str(source), '--integration', 'codex'], source)
        fixture_runtime(source)
        schema_runtime.record_copy(source)
        ignore = source/'.gitignore'
        with ignore.open('a', encoding='utf-8') as stream: stream.write('\n.specify/\n.agents/\nartifacts/\n')
        (source/'note.txt').write_text('retained consumer output\n', encoding='utf-8')
        flow.git(source, 'add', '.')
        flow.git(source, '-c', 'user.name=Package Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Known installed consumer')
        before_inspection = flow.installation_inputs(source)
        if flow.inventory(source)['customizations']:
            raise AssertionError('Native preset rendering was misclassified as consumer customization')
        if flow.installation_inputs(source) != before_inspection:
            raise AssertionError('Read-only native preset assessment mutated installation')
        implementation_skill = source/'.agents/skills/speckit-implement/SKILL.md'
        pristine = implementation_skill.read_bytes()
        implementation_skill.write_bytes(pristine + b'\nConsumer manual extension\n')
        if '.agents/skills/speckit-implement/SKILL.md' not in flow.inventory(source)['customizations']:
            raise AssertionError('Native preset ownership concealed a consumer skill edit')
        implementation_skill.write_bytes(pristine)  # Explicit fixture repair; no real consumer edits.
        adapter = release/'scripts/consumer_upgrade_workspace.py'
        original = flow.installation_inputs(source)
        prepared = json.loads(run([sys.executable, str(adapter), 'prepare', '--source', str(source), '--target', str(target),
                                   '--release-root', str(release), '--branch', 'qualified-upgrade'], source))
        if prepared['sourceCommit'] != flow.git(source, 'rev-parse', 'HEAD'): raise AssertionError('Preparation lost the known commit')
        if flow.installation_inputs(source) != original: raise AssertionError('Preparation mutated source setup')
        fixture_runtime(target)  # Explicit local preparation after baseline reproduction.
        installed = json.loads(run([sys.executable, str(adapter), 'install', '--target', str(target), '--release-root', str(release), '--offline'], target))
        if installed['updaterExitCode'] != 0:
            logs = '\n'.join((target/p).read_text(encoding='utf-8') for p in installed['updaterEvidence'])
            raise AssertionError('Real isolated updater did not converge: ' + logs)
        check_installed_workflow(target)
        if flow.installation_inputs(source) != original: raise AssertionError('Isolated installation changed source')
        checks = [{'id': 'retained-behavior', 'command': [sys.executable, '-c',
                  "from pathlib import Path; assert Path('note.txt').read_text() == 'retained consumer output\\n'"]}]
        target_checks = target/'artifacts/qualification-checks.json'
        flow.atomic(target_checks, checks)
        installed_cli = target/'.specify/extensions/program-kit-governance/scripts/consumer_upgrade.py'
        run([sys.executable, str(installed_cli), 'assess'], target)
        run([sys.executable, str(installed_cli), 'verify', '--input', 'artifacts/qualification-checks.json'], target)
        run([sys.executable, str(adapter), 'integrate', '--target', str(target), '--destination', str(source)], target)
        flow.git(target, 'add', '.')
        flow.git(target, '-c', 'user.name=Package Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Reviewed isolated upgrade')
        flow.git(source, 'merge', '--ff-only', flow.git(target, 'rev-parse', 'HEAD'))
        # A real updater succeeds, then required destination verification fails. The
        # adapter must preserve diagnostics and restore exact old ignored installation.
        before_failed_activation = flow.installation_inputs(source)
        flow.atomic(source/'artifacts/qualification-checks.json',
                    [{'id': 'required-failure', 'command': [sys.executable, '-c', 'raise SystemExit(9)']}])
        run([sys.executable, str(adapter), 'activate', '--target', str(target), '--destination', str(source),
             '--release-root', str(release), '--input', 'artifacts/qualification-checks.json', '--offline'], source,
            expected_exit=2)
        if flow.installation_inputs(source) != before_failed_activation:
            raise AssertionError('Failed actual destination activation did not restore exact installation')
        ledgers = list((source/'artifacts/program-kit/consumer-activation').glob('*/activation.json'))
        if len(ledgers) != 1 or flow.read(ledgers[0])['status'] != 'recovered':
            raise AssertionError('Actual failed activation recovery was not sealed')
        if (source/'note.txt').read_text() != 'retained consumer output\n':
            raise AssertionError('Actual recovery changed consumer behavior')
        flow.atomic(source/'artifacts/qualification-checks.json', checks)
        result = json.loads(run([sys.executable, str(adapter), 'activate', '--target', str(target), '--destination', str(source),
                                 '--release-root', str(release), '--input', 'artifacts/qualification-checks.json', '--offline'], source))
        if not result['activated'] or result['applicationAcceptanceEstablished']:
            raise AssertionError('Actual destination activation verdict is incorrect: ' + str(result))
        state = flow.load(source)
        if state['checks'][0]['executionRoot'] != str(source): raise AssertionError('Old worktree checks were relabeled destination evidence')
        if (source/'note.txt').read_text() != 'retained consumer output\n': raise AssertionError('Consumer behavior changed')
        # Inspect merged native templates and skills at the destination too:
        # updater convergence alone cannot prove operation-based instructions.
        check_installed_workflow(source)
        # Keep a small durable qualification summary after owned fixture cleanup.
        flow.atomic(ROOT/'artifacts/consumer-upgrade-install.json', {'schemaVersion': 1, 'version': version,
            'packagedPrimitiveInstallation': True, 'isolatedUpdaterConverged': True, 'actualDestinationActivated': True,
            'sourceProtectedDuringPreparation': True, 'destinationChecksExecuted': True,
            'actualFailedActivationRecovered': True,
            'installedOperationWorkflowVerifiedAfterUpgrade': True,
            'applicationBehaviorTested': 'Retained named file output in this disposable minimal consumer',
            'applicationAcceptanceEstablished': False, 'codingAgentsStarted': False})
    print('Packaged consumer preparation, real sequential updater and actual destination activation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
