"""One real packaged updater journey from the immediate supported predecessor.

The old sources come from Git's exact tag, not fabricated version metadata. No
network package lookup, coding agent, native application build or publication.
"""
from __future__ import annotations

import json
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from owned_fixture import FixtureDirectory, native_path
from validate_package_smoke import extract
from local_bundle_fixture import install_local_bundle, verify_release_copies

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = next(entry['previous'] for entry in json.loads((ROOT / 'releases/history.json').read_text(encoding='utf-8'))['entries']
                if entry['version'] == (ROOT / 'VERSION').read_text().strip())


def inactive_setup(project, previous):
    """Fictional withdrawn history and reviewed source; no consumer acceptance."""
    import validate_inactive_upgrade as inactive
    original_catalog = inactive.fixture.CATALOG
    seed = inactive.InactiveUpgradeTests('test_active_guards_and_explicit_tooling_apply_are_separate_and_idempotent')
    try:
        inactive.fixture.CATALOG = previous / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'
        seed.setUp()
        for path in seed.root.rglob('*'):
            if path.is_file():
                target = project / path.relative_to(seed.root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        selection = inactive.blocks.load_json(project / inactive.history.SELECTION)
        inactive.blocks.preserve_dependency_profile(project, selection, inactive.fixture.CATALOG)
        managed = inactive.blocks.load_json(project / '.program-kit/managed.json')
        managed['programKitVersion'] = PREVIOUS
        inactive.write(project, '.program-kit/managed.json', managed)
        contract = seed.contract
    finally:
        inactive.fixture.CATALOG = original_catalog
        seed.doCleanups()
    for path in (project / '.program-kit/dependency-profiles').rglob('*'):
        if path.is_file(): contract['inputs'][path.relative_to(project).as_posix()] = inactive.history.sha(path)
    contract['inputs'][inactive.history.PROFILE] = inactive.history.sha(project / inactive.history.PROFILE)
    declaration = inactive.write(project, 'artifacts/review/history.json', contract)
    source_relative = '.specify/extensions/program-kit-governance/scripts/tooling_witness.py'
    source = project / source_relative
    before = inactive.history.sha(source)
    source.write_bytes(source.read_bytes() + b'\n# Fictional reviewed source annotation for argument transport.\n')
    module = inactive.write(project, 'artifacts/review/repaired_witness.py', (
        'import unittest, runpy, hashlib\nfrom pathlib import Path\n'
        'class Witness(unittest.TestCase):\n'
        ' def test_current_hash_behavior(self):\n'
        '  scope = runpy.run_path(str(Path.cwd() / ' + repr(source_relative) + '))\n'
        '  self.assertEqual(hashlib.sha256(b"transport fixture").hexdigest(), scope["sha"](b"transport fixture"))\n'
    ).encode())
    case = 'repaired_witness.Witness.test_current_hash_behavior'
    cases = inactive.write(project, 'artifacts/review/cases.json', {'schemaVersion': 1,
        'inputs': [source_relative], 'modules': [{'module': 'repaired_witness', 'path': module.relative_to(project).as_posix(),
        'sha256': inactive.history.sha(module), 'cases': {case: ['Windows', 'Linux']}}]})
    repairs = inactive.write(project, 'artifacts/review/repairs.json', {'schemaVersion': 1,
        'contract': cases.relative_to(project).as_posix(), 'contractSha256': inactive.history.sha(cases),
        'repairs': [{'path': source_relative, 'beforeSha256': before, 'afterSha256': inactive.history.sha(source),
                    'requiredCases': [case], 'rationale': 'Fictional source annotation; execute actual hash behavior before replacement.'}]})
    engineering = previous / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/Build.ps1'
    original = engineering.read_bytes()
    managed = inactive.blocks.load_json(project / '.program-kit/managed.json')
    digest = hashlib.sha256(original).hexdigest()
    managed['files']['eng/Build.ps1'] = {'ownership': 'managed', 'sourceIdentity': 'files/eng/Build.ps1',
        'templateHash': digest, 'lastWrittenHash': digest}
    inactive.write(project, '.program-kit/managed.json', managed)
    inactive.write(project, 'eng/Build.ps1', original + b'\n# Fictional consumer conflict must reject.\n')
    preserved = {name: inactive.history.sha(project / name) for name in contract['inputs']}
    return (['--inactive-history', declaration.relative_to(project).as_posix(), '--inactive-history-sha256', inactive.history.sha(declaration),
             '--local-repairs', repairs.relative_to(project).as_posix(), '--local-repairs-sha256', inactive.history.sha(repairs)], preserved, original)


def scenario(*, inactive=False):
    import specify_cli
    import yaml
    sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
    import schema_runtime
    version = (ROOT / 'VERSION').read_text().strip()
    archive = ROOT / 'artifacts' / f'program-kit-{version}.zip'
    if not archive.is_file():
        raise AssertionError('Build the actual candidate archives before the upgrade fixture')
    runtime = schema_runtime.runtime_path(ROOT)
    if not (runtime / '.ready').is_file():
        raise AssertionError('Prepare the exact schema runtime before the upgrade fixture')
    evidence = ROOT / 'artifacts/tests/packaged-upgrade' / uuid.uuid4().hex[:12]
    evidence.mkdir(parents=True)
    steps = []
    started = time.monotonic()
    with FixtureDirectory() as directory:
        owned = Path(directory)
        project = owned / 'consumer app'
        project.mkdir()
        previous, release = owned / 'previous', owned / 'candidate'
        historical = owned / 'historical.zip'
        archived = subprocess.run(['git', 'archive', '--format=zip', '--output=' + native_path(historical),
            'v' + PREVIOUS, 'VERSION', 'bundle.yml', 'extensions', 'presets', 'workflows'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
        if archived.returncode:
            raise AssertionError('Historical fixture requires the actual local v' + PREVIOUS + ' tag: ' + archived.stderr)
        extract(historical, previous)
        extract(archive, release)
        site = Path(specify_cli.__file__).parent.parent
        bridge = [sys.executable, native_path(release / 'scripts/invoke_specify.py'), '--site-packages', str(site), '--']
        scratch = owned / 'tmp'
        scratch.mkdir()
        environment = dict(os.environ, SPECIFY_INIT_DIR=native_path(project),
            PROGRAM_KIT_SPECIFY_SITE_PACKAGES=str(site), PYTHONUTF8='1',
            TEMP=native_path(scratch), TMP=native_path(scratch), TMPDIR=native_path(scratch))

        def run(label, command, expected=0):
            step_started = time.monotonic()
            result = subprocess.run([str(x) for x in command], cwd=native_path(project), env=environment,
                capture_output=True, text=True, encoding='utf-8', timeout=90)
            for stream in ('stdout', 'stderr'):
                (evidence / (label + '.' + stream + '.log')).write_text(getattr(result, stream), encoding='utf-8')
            steps.append({'id': label, 'exitCode': result.returncode,
                'elapsedSeconds': round(time.monotonic() - step_started, 3)})
            (evidence / 'steps.json').write_text(json.dumps(steps, indent=2))
            if result.returncode != expected:
                raise AssertionError(label + ' failed; inspect ' + str(evidence) + '\n' + result.stdout + result.stderr)
            return result

        run('init', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'copilot',
            '--script', 'py', '--ignore-agent-tools'])
        # Core owns first-install contribution records; preinstalling primitives
        # and fabricating ownership would not represent a supported consumer.
        install_local_bundle(project, previous, bridge, run, integration='copilot')
        prepared = schema_runtime.runtime_path(project)
        prepared.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(runtime, prepared)
        schema_runtime.record_copy(project)
        authored = {'consumer-notes.txt': b'Authored consumer output must survive.\n',
            'specs/001-existing/spec.md': b'# Existing consumer feature\nRetain its decisions.\n'}
        for relative, payload in authored.items():
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        extra, preserved, original_engineering = inactive_setup(project, previous) if inactive else ([], {}, None)
        command = [sys.executable, native_path(release / 'scripts/upgrade_program_kit.py'),
            '--release-root', native_path(release), '--target', native_path(project), '--integration', 'copilot',
            '--offline', '--specify-command-json', json.dumps(bridge), *extra]
        if inactive:
            run('inactive-preview', [*command, '--plan'])
            failed = run('inactive-managed-conflict', command, expected=2)
            assert 'conflict' in (failed.stdout + failed.stderr).lower()
            attempts = list((project / 'artifacts/program-kit/runs').glob('*/upgrade-attempt.json'))
            assert any(json.loads(path.read_text())['status'] == 'incomplete' for path in attempts)
            (project / 'eng/Build.ps1').write_bytes(original_engineering)
        run('packaged-updater', command)
        for relative, payload in authored.items():
            assert (project / relative).read_bytes() == payload, 'Updater changed authored input: ' + relative
        records = json.loads((project / '.specify/bundle-records.json').read_text())
        record = next(row for row in records['bundles'] if row['bundle_id'] == 'program-kit')
        assert record['version'] == version
        assert all(row['version'] == version for row in record['contributed_components'])
        for kind, name, key, filename in [
                *[('extensions', 'program-kit-' + name, 'extension', 'extension.yml')
                  for name in ('governance', 'building-blocks', 'dotnet')],
                ('presets', 'program-kit-governance-preset', 'preset', 'preset.yml'),
                ('workflows', 'program-kit-bootstrap', 'workflow', 'workflow.yml')]:
            actual = yaml.safe_load((project / '.specify' / kind / name / filename).read_text())
            assert actual[key]['version'] == version, 'Component did not advance: ' + name
        migration = json.loads((project / '.program-kit/installation/migration.json').read_text())
        assert migration['fromVersion'] == PREVIOUS and migration['toVersion'] == version
        assert migration['checks']['installation-coherence'] is True
        assert migration['migrationCompletionEstablished'] is True
        if inactive:
            assert migration['migrationScope'] == 'tooling-only-inactive-history'
            assert migration['scopedMigrationCompletionEstablished'] is True
            assert migration['designAcceptanceEstablished'] is False
            assert migration['destinationActivationEstablished'] is False
            assert migration['localRepairs']['execution']['executedCases']['repaired_witness.Witness.test_current_hash_behavior'] == 'passed'
            assert preserved == {p: hashlib.sha256((project / p).read_bytes()).hexdigest() if (project / p).is_file() else None for p in preserved}
            # A completed attempt is not an interrupted retry. Its old declaration
            # cannot be reused to admit source bytes that are no longer installed.
            rejected = run('inactive-completed-declaration-reuse', command, expected=2)
            assert 'reviewed after hash' in rejected.stderr
            assert preserved == {p: hashlib.sha256((project / p).read_bytes()).hexdigest() if (project / p).is_file() else None for p in preserved}
        # Copilot supports dev symlinks on POSIX. A release upgrade must leave
        # ordinary native outputs, independently usable after staging is gone.
        verify_release_copies(project, release)
    result = {'status': 'passed', 'fromVersion': PREVIOUS, 'toVersion': version,
        'elapsedSeconds': round(time.monotonic() - started, 3), 'steps': steps,
        'inactiveHistory': inactive,
        'scope': 'Actual immutable-tag source installation to packaged sequential updater; authored data preserved. No application acceptance.'}
    (evidence / 'result.json').write_text(json.dumps(result, indent=2))
    print('Packaged updater journey: ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inactive-history', action='store_true', help='Fictional withdrawn design plus freshly executed local repair transport')
    scenario(inactive=parser.parse_args().inactive_history)
