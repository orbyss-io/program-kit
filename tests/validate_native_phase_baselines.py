"""Immediate-predecessor source coverage and optional actual-public-byte admission.

--public-bundle accepts an already downloaded previous public bundle. It performs
read-only source admission in an extracted, Git-free candidate authority; it
neither runs an initializer nor starts an agent or downloads packages.
Adding --candidate-bundle runs one native first-install copilot consumer upgrade
from those same public originals, using local transports and a prepared schema
runtime. It preserves agent-context variables and never starts an initializer.
"""
from pathlib import Path
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_native_phase_baselines as baselines
import native_phase_ownership as ownership
from owned_fixture import FixtureDirectory
from validate_package_smoke import extract


class PreviousReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = json.loads(baselines.OUTPUT.read_text(encoding='utf-8'))
        history = json.loads((ROOT / 'releases/history.json').read_text(encoding='utf-8'))
        version = (ROOT / 'VERSION').read_text().strip()
        cls.previous = next(row['previous'] for row in history['entries'] if row['version'] == version)

    def test_shipped_catalog_covers_complete_immediate_predecessor(self):
        baselines.validate_previous(ROOT, self.table)

    def test_older_supported_witnesses_do_not_substitute_for_missing_predecessor(self):
        table = copy.deepcopy(self.table)
        table['components'] = [row for row in table['components'] if row['version'] != self.previous]
        with self.assertRaisesRegex(ValueError, 'Missing exact previous-release native source witness'):
            baselines.validate_previous(ROOT, table)

    def test_a_manifest_alone_or_partial_source_list_cannot_satisfy_packaging(self):
        table = copy.deepcopy(self.table)
        for row in table['components']:
            if row['version'] == self.previous and row['id'] == 'program-kit-governance':
                row['files'] = {'extension.yml': row['manifestSha256']}
        with self.assertRaisesRegex(ValueError, 'program-kit-governance'):
            baselines.validate_previous(ROOT, table)

    def test_missing_history_identifies_the_fetch_prerequisite(self):
        with patch.object(baselines, 'capture', side_effect=subprocess.CalledProcessError(128, ['git'])):
            with self.assertRaisesRegex(ValueError, 'fetch the supported release tag'):
                baselines.validate_previous(ROOT, self.table)

    def test_builder_rejects_missing_predecessor_before_creating_publication_output(self):
        import build_release
        table = copy.deepcopy(self.table)
        table['components'] = [row for row in table['components'] if row['version'] != self.previous]
        validate = baselines.validate_previous
        with FixtureDirectory() as directory:
            output = Path(directory) / 'must not be emitted'
            with patch.object(sys, 'argv', ['build_release.py', '--output', str(output)]), \
                    patch.object(baselines, 'validate_previous', side_effect=lambda root: validate(root, table)):
                with self.assertRaisesRegex(ValueError, 'Missing exact previous-release native source witness'):
                    build_release.main()
            self.assertFalse(output.exists())


def public_sources(archive):
    from specify_cli.extensions import ExtensionManifest
    from specify_cli.presets import PresetManifest
    with FixtureDirectory() as directory:
        fixture = Path(directory)
        release = fixture / 'extracted candidate'
        component = release / 'extensions/program-kit-governance'
        (component / 'references').mkdir(parents=True)
        (component / 'scripts').mkdir()
        shutil.copyfile(baselines.OUTPUT, component / 'references/native-phase-source-baselines.json')
        shutil.copyfile(ROOT / 'extensions/program-kit-governance/scripts/asset_sources.py',
                        component / 'scripts/asset_sources.py')
        previous = fixture / 'actual public sources'
        extract(archive, previous)
        target = fixture / 'consumer'
        admitted = {}
        for kind, identity, filename in baselines.COMPONENTS:
            installed = target / '.specify' / kind / identity
            installed.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(previous / kind / identity, installed)
            manifest = (ExtensionManifest if kind == 'extensions' else PresetManifest)(installed / filename)
            metadata = {'version': manifest.version, 'manifest_hash': manifest.get_hash()}
            sources = sorted(ownership.installed_source_files(installed, release))
            before = {name: ownership.digest(ownership.asset_reader(release).read(installed / name)) for name in sources}
            if identity == 'program-kit-governance':
                # Reproduce the original omission against the same authentic
                # package. An extracted release cannot borrow nearby Git tags.
                catalog = component / 'references/native-phase-source-baselines.json'
                corrected = catalog.read_bytes()
                old = json.loads(corrected)
                old['components'] = [row for row in old['components'] if row['version'] != manifest.version]
                catalog.write_text(json.dumps(old), encoding='utf-8')
                try:
                    with unittest.TestCase().assertRaisesRegex(ownership.OwnershipError, 'one authenticated original'):
                        ownership.source_guard(target, release, identity, metadata, manifest, sources, kind)
                finally:
                    catalog.write_bytes(corrected)
            admitted[identity] = ownership.source_guard(target, release, identity, metadata, manifest, sources, kind)
            assert admitted[identity] == before, 'Admission must be read-only and bind every original source'
            if kind == 'extensions' and identity == 'program-kit-governance':
                command = installed / 'commands/speckit.program-kit-governance.architecture.md'
                original = command.read_bytes()
                customized = original + b'\nConsumer customization must remain protected.\n'
                command.write_bytes(customized)
                try:
                    with unittest.TestCase().assertRaisesRegex(ownership.OwnershipError, 'customized.*architecture.md'):
                        ownership.source_guard(target, release, identity, metadata, manifest, sources, kind)
                    assert command.read_bytes() == customized, 'Rejection changed consumer-authored bytes'
                finally:
                    command.write_bytes(original)
                helper = installed / 'scripts/phase_obligations.py'
                original = helper.read_bytes(); helper.unlink()
                try:
                    with unittest.TestCase().assertRaisesRegex(ownership.OwnershipError, 'customized.*phase_obligations.py'):
                        ownership.source_guard(target, release, identity, metadata, manifest,
                                               sorted(ownership.installed_source_files(installed, release)), kind)
                    assert not helper.exists(), 'Read-only admission recreated missing consumer source'
                finally:
                    helper.write_bytes(original)
        print('Actual public sources admitted without Git; custom source and missing helper refused: '
              + ', '.join(f'{identity}={len(files)}' for identity, files in admitted.items()))


def public_upgrade(archive, candidate):
    """One real prior-public copilot consumer, real updater, local transports only."""
    import specify_cli
    from local_bundle_fixture import install_local_bundle
    from validate_public_upgrade import installed_versions
    diagnostics = ROOT / 'artifacts/release-repair/public-upgrade' / uuid.uuid4().hex
    diagnostics.mkdir(parents=True)
    started = time.monotonic()
    with FixtureDirectory() as directory:
        fixture = Path(directory)
        previous, release, project = (fixture / name for name in ('prior public package', 'corrected package', 'copilot consumer'))
        extract(archive, previous); extract(candidate, release); project.mkdir()
        temporary = fixture / 'owned process temp'; temporary.mkdir()
        environment = {**os.environ, 'TEMP': str(temporary), 'TMP': str(temporary), 'PYTHONUTF8': '1'}
        bridge = [sys.executable, ROOT / 'scripts/invoke_specify.py', '--site-packages',
                  Path(specify_cli.__file__).parent.parent, '--']
        def run(label, command):
            remaining = 120 - (time.monotonic() - started)
            assert remaining > 0, 'Prior-public upgrade exceeded its 120-second family budget'
            result = subprocess.run([str(item) for item in command], cwd=project, env=environment,
                                    capture_output=True, text=True, encoding='utf-8', timeout=remaining)
            (diagnostics / (label + '.stdout.log')).write_text(result.stdout, encoding='utf-8')
            (diagnostics / (label + '.stderr.log')).write_text(result.stderr, encoding='utf-8')
            if result.returncode:
                raise AssertionError(f'{label} failed: {result.stdout}\n{result.stderr}')
            return result
        run('initialize', [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'copilot',
                           '--script', 'py', '--ignore-agent-tools'])
        # Native first install owns contribution records; no primitive pre-seal shortcut.
        install_local_bundle(project, previous, bridge, run, integration='copilot')
        previous_version = (previous / 'VERSION').read_text().strip()
        assert set(installed_versions(project).values()) == {previous_version}
        with patch('tempfile.tempdir', str(temporary)):
            original = ownership.preflight(project, release)
        assert original['readOnly'] and original['extensionSourceSha256']
        authored = project / 'authored-consumer.txt'
        authored.write_bytes(b'Exact consumer bytes must survive the prior-public upgrade.\n')
        before = authored.read_bytes()
        runtime_source = ROOT / 'extensions/program-kit-governance/scripts/schema_runtime.py'
        spec = importlib.util.spec_from_file_location('public_upgrade_prepared_runtime', runtime_source)
        runtime = importlib.util.module_from_spec(spec); spec.loader.exec_module(runtime)
        target_runtime = runtime.runtime_path(project)
        target_runtime.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(runtime.runtime_path(ROOT), target_runtime)
        runtime.record_copy(project)
        run('upgrade', [sys.executable, release / 'scripts/upgrade_program_kit.py', '--release-root', release,
                        '--target', project, '--integration', 'copilot', '--offline',
                        '--specify-command-json', json.dumps([str(item) for item in bridge])])
        version = (release / 'VERSION').read_text().strip()
        assert set(installed_versions(project).values()) == {version}
        assert authored.read_bytes() == before
        run('installed-check', [sys.executable, project / '.specify/extensions/program-kit-governance/scripts/governance_state.py',
                                'validate-installation'])
    elapsed = time.monotonic() - started
    assert elapsed <= 120, 'Prior-public upgrade exceeded its 120-second family budget'
    (diagnostics / 'result.json').write_text(json.dumps({'status': 'passed', 'seconds': elapsed,
        'previous': previous_version, 'current': version, 'integration': 'copilot',
        'priorPublicBundleSha256': ownership.digest(archive.read_bytes()),
        'candidateBundleSha256': ownership.digest(candidate.read_bytes())}, indent=2) + '\n', encoding='utf-8')
    print(f'Actual public {previous_version} -> corrected {version} copilot upgrade passed in {elapsed:.3f}s; {diagnostics}')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--public-bundle' and sys.argv[3] == '--candidate-bundle':
        public_upgrade(Path(sys.argv[2]).resolve(strict=True), Path(sys.argv[4]).resolve(strict=True))
    elif len(sys.argv) == 3 and sys.argv[1] == '--public-bundle':
        public_sources(Path(sys.argv[2]).resolve(strict=True))
    else:
        unittest.main()
