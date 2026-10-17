"""One real packaged updater journey from immutable locally available v0.13.1.

The old sources come from Git's exact tag, not fabricated version metadata. No
network package lookup, coding agent, native application build or publication.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from owned_fixture import FixtureDirectory, native_path
from validate_package_smoke import extract
from local_bundle_fixture import install_local_bundle

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = '0.13.1'


def scenario():
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
        project = owned / 'supported consumer with spaces'
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

        def run(label, command):
            step_started = time.monotonic()
            result = subprocess.run([str(x) for x in command], cwd=native_path(project), env=environment,
                capture_output=True, text=True, encoding='utf-8', timeout=90)
            for stream in ('stdout', 'stderr'):
                (evidence / (label + '.' + stream + '.log')).write_text(getattr(result, stream), encoding='utf-8')
            steps.append({'id': label, 'exitCode': result.returncode,
                'elapsedSeconds': round(time.monotonic() - step_started, 3)})
            (evidence / 'steps.json').write_text(json.dumps(steps, indent=2))
            if result.returncode:
                raise AssertionError(label + ' failed; inspect ' + str(evidence) + '\n' + result.stdout + result.stderr)
            return result

        run('init', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex',
            '--script', 'py', '--ignore-agent-tools'])
        # Core owns first-install contribution records; preinstalling primitives
        # and fabricating ownership would not represent a supported consumer.
        install_local_bundle(project, previous, bridge, run)
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
        run('packaged-updater', [sys.executable, native_path(release / 'scripts/upgrade_program_kit.py'),
            '--release-root', native_path(release), '--target', native_path(project), '--integration', 'codex',
            '--offline', '--specify-command-json', json.dumps(bridge)])
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
    result = {'status': 'passed', 'fromVersion': PREVIOUS, 'toVersion': version,
        'elapsedSeconds': round(time.monotonic() - started, 3), 'steps': steps,
        'scope': 'Actual immutable-tag source installation to packaged sequential updater; authored data preserved. No application acceptance.'}
    (evidence / 'result.json').write_text(json.dumps(result, indent=2))
    print('Packaged updater journey: ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    scenario()
