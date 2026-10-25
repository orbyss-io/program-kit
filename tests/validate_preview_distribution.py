"""Synthetic preview identity/channel, refusal, and real native toolkit refresh; no agents."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from owned_fixture import FixtureDirectory
from local_bundle_fixture import install_local_bundle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import product_version as versions
import upgrade_program_kit as updater
from publish_candidate import channel_arguments
from build_release import bundle_source_files
from build_release_guidance import build as guidance
from release_assets import artifact_records, sha256


def run(root, argv):
    result = subprocess.run(list(map(str, argv)), cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=120)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


def version_release(root, version):
    old = (root / 'VERSION').read_text().strip()
    for name in ('VERSION', 'bundle.yml', *(kind + '/' + identity + '/' + ('extension.yml' if kind == 'extensions' else 'preset.yml')
                                           for kind, identity in updater.COMPONENTS)):
        path = root / name
        path.write_text(path.read_text().replace(old, version), encoding='utf-8')


class PreviewDistribution(unittest.TestCase):
    def test_retired_engines_are_uniformly_excluded_but_selected_technical_inputs_remain(self):
        from build_release import RETIRED_GOVERNANCE_SCRIPTS, deterministic_zip, install_asset
        import zipfile
        with FixtureDirectory() as temporary:
            root = Path(temporary)
            (root / 'extension.yml').write_text('extension:\n  id: program-kit-governance\n', encoding='utf-8')
            scripts = root / 'scripts'; scripts.mkdir()
            for name in (*RETIRED_GOVERNANCE_SCRIPTS, 'product_intake.py', 'bootstrap_provider_context.py'):
                (scripts / name).write_text('# synthetic module\n', encoding='utf-8')
            archive = root / 'component.zip'
            deterministic_zip(root, archive)
            with zipfile.ZipFile(archive) as payload:
                names = set(payload.namelist())
            self.assertIn('scripts/product_intake.py', names)
            self.assertIn('scripts/bootstrap_provider_context.py', names)
            for name in RETIRED_GOVERNANCE_SCRIPTS:
                self.assertNotIn('scripts/' + name, names)
                self.assertFalse(install_asset(ROOT, Path('extensions/program-kit-governance/scripts') / name))
            copied = set(bundle_source_files(ROOT))
            self.assertIn(Path('extensions/program-kit-governance/scripts/managed_provider_probes.py'), copied)
            self.assertIn(Path('extensions/program-kit-governance/scripts/product_intake.py'), copied)
            self.assertFalse(any(path.name in RETIRED_GOVERNANCE_SCRIPTS and 'program-kit-governance' in path.parts for path in copied))

    def test_obsolete_authority_routes_refuse_without_mutation_or_provider_io(self):
        with FixtureDirectory() as temporary:
            root = Path(temporary)
            retained = root / 'historical.json'; retained.write_bytes(b'\xff original historical bytes')
            before = retained.read_bytes()
            scripts = ROOT / 'extensions/program-kit-governance/scripts'
            for name, call in (('inactive_history', lambda module: module.validate(root, 'historical.json', 'a'*64, None)),
                               ('provider_operation', lambda module: module.native_admission(root, {}, 'old', 'old.py')),
                               ('codex_worker_policy', lambda module: module.worker_environment(root, 'codex').__enter__())):
                module = updater.load_module(scripts / (name + '.py'), 'preview_retired_' + name)
                with patch('subprocess.run', side_effect=AssertionError('Retired authority executed a command')):
                    with self.assertRaisesRegex(ValueError, 'retired|unavailable'):
                        call(module)
                self.assertEqual(before, retained.read_bytes())
                self.assertEqual([retained], list(root.iterdir()))
            sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
            profiles = updater.load_module(ROOT / 'extensions/program-kit-building-blocks/scripts/dependency_profiles.py', 'preview_retired_profile')
            ledger = root / 'docs/architecture/bootstrap-prerequisites.json'
            ledger.parent.mkdir(parents=True)
            ledger.write_bytes(b'\xff old ledger; not parsed or rewritten')
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'Retired bootstrap'):
                profiles.accept(root, root / 'missing-transition', root / 'missing-registry', 'decision', 'reason')
            self.assertEqual(before, {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_identity_numeric_preview_order_and_publisher_channel(self):
        self.assertLess(versions.order('1.0.0-preview.2'), versions.order('1.0.0-preview.10'))
        self.assertLess(versions.order('1.0.0-preview.10'), versions.order('1.0.0'))
        self.assertEqual(['--prerelease', '--latest=false'], channel_arguments('1.0.0-preview.1'))
        self.assertEqual([], channel_arguments('1.0.0'))
        for value in ('1.0.0-preview.01', '1.0.0-unsafe', 'v1.0.0-preview.1', '1.0.0-preview.1;echo'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                versions.parse(value)

    def test_initializer_admits_exact_preview_tag_and_rejects_unsafe_tags(self):
        import initialize_device
        with patch.object(initialize_device, 'check') as check:
            initialize_device.initialize(ROOT, 'v1.0.0-preview.1', ROOT)
            check.assert_called_once()
        for value in ('v1.0.0-preview.01', 'v1.0.0-preview.1/../other', 'main'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                initialize_device.initialize(ROOT, value, ROOT)

    def test_0x_boundary_refuses_before_mutation(self):
        with FixtureDirectory(prefix='preview-reonboard-', native=True) as temporary:
            target = Path(temporary)
            manifest = target / '.specify/extensions/program-kit-governance/extension.yml'
            manifest.parent.mkdir(parents=True)
            manifest.write_text('extension:\n  version: "0.14.3"\n')
            authored = target / 'docs/architecture/product.md'
            authored.parent.mkdir(parents=True)
            authored.write_text('Fictional authored product and decisions\n')
            before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(updater.UpgradeError, 'PKU160.*re-onboarding'):
                updater.refresh(target, ROOT, None)
            self.assertEqual(before, {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()})

    def test_configuration_exception_does_not_hide_nested_user_sources(self):
        with FixtureDirectory(prefix='preview-config-ownership-', native=True) as temporary:
            root = Path(temporary)
            (root / 'consumer-config.yml').write_text('Native preserved root configuration\n')
            (root / 'scripts').mkdir()
            (root / 'scripts/consumer-config.yml').write_text('Authored nested source must cause refusal, not be discarded\n')
            self.assertEqual({'scripts/consumer-config.yml'}, set(updater.source_files(root)))

    def test_preview_guidance_and_exact_asset_inventory_need_no_0x_migrations(self):
        with FixtureDirectory(prefix='preview-assets-', native=True) as temporary:
            root = Path(temporary)
            history = (ROOT / 'releases/history.json').read_bytes()
            staged = guidance(ROOT, root / 'guidance', '1.0.0-preview.1')
            self.assertEqual({'COMPATIBILITY.md', 'RELEASE-NOTES.md'}, {path.name for path in staged.iterdir()})
            self.assertEqual(history, (ROOT / 'releases/history.json').read_bytes())
            version = '1.0.0-preview.1'
            names = ['program-kit-governance', 'program-kit-building-blocks', 'program-kit-dotnet',
                     'program-kit-governance-preset', 'program-kit', 'program-kit-tooling']
            files = [root / (name + '-' + version + '.zip') for name in names]
            files += [root / ('Initialize-ProgramKit-' + version + suffix) for suffix in ('.cmd', '.sh')]
            files += [root / ('RELEASE-NOTES-' + version + '.md'), root / ('COMPATIBILITY-' + version + '.md')]
            for path in files:
                path.write_bytes(b'Fictional inspected candidate bytes: ' + path.name.encode())
            profile = root / ('dependency-profile-index-' + version + '.json')
            profile.write_text(json.dumps({'schemaVersion': 1, 'profiles': []}))
            files.append(profile)
            (root / 'SHA256SUMS').write_text(''.join(sha256(path) + '  ' + path.name + '\n' for path in files))
            self.assertEqual({path.name for path in [*files, root / 'SHA256SUMS']},
                             {Path(row['path']).name for row in artifact_records(root, version)})
            files[0].write_bytes(b'Changed after candidate inspection')
            with self.assertRaisesRegex(RuntimeError, 'differs from its checksum'):
                artifact_records(root, version)

    def test_publisher_sets_preview_channel_on_create_and_retry_without_publication(self):
        import publish_candidate as publication
        with FixtureDirectory(prefix='preview-publisher-', native=True) as temporary:
            root = Path(temporary)
            identity = {'version': '1.0.0-preview.1', 'commit': 'a' * 40}
            promotion = {'source': identity, 'assets': [], 'runId': 123}
            (root / 'promotion.json').write_text(json.dumps(promotion))
            (root / 'payload').mkdir()
            (root / 'payload/candidate-payload.json').write_text('{}')
            (root / 'payload/RELEASE-NOTES-1.0.0-preview.1.md').write_text('Fictional approved notes')
            existing = {'prerelease': True, 'assets': []}
            with patch.object(publication, 'source', return_value=identity), patch.object(publication, 'git', return_value='a' * 40), \
                    patch.object(publication, 'api', return_value={'object': {'type': 'commit', 'sha': 'a' * 40}}), \
                    patch.object(publication, 'verify_payload'), patch.object(publication, 'existing_release', side_effect=[None, existing, existing]), \
                    patch.object(publication, 'gh') as gh:
                publication.publish('v1.0.0-preview.1', root)
            calls = [list(call.args) for call in gh.call_args_list]
            for operation in ('create', 'edit'):
                command = next(command for command in calls if command[:2] == ['release', operation])
                self.assertIn('--prerelease', command)
                self.assertIn('--latest=false', command)

    def test_native_preview_refresh_preserves_authored_work_and_refuses_customizations(self):
        with FixtureDirectory(prefix='preview-native-refresh-', native=True) as temporary:
            owned = Path(temporary)
            previous, release, target = owned / 'previous', owned / 'release', owned / 'consumer'
            for directory in (previous, release, target):
                directory.mkdir()
            for relative in bundle_source_files(ROOT):
                for destination in (previous, release):
                    path = destination / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / relative, path)
            version_release(release, '1.0.0-preview.2')
            import specify_cli
            site = Path(specify_cli.__file__).parent.parent
            bridge = [sys.executable, previous / 'scripts/invoke_specify.py', '--site-packages', site, '--']
            run(target, [*bridge, 'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'])
            install_local_bundle(target, previous, bridge, lambda label, argv: run(target, argv))
            authored = {'docs/architecture/product.md': 'Fictional product intent\n',
                        'specs/001-request/spec.md': 'Normal authored specification\n',
                        'src/Application.py': 'print("consumer work")\n',
                        'eng/packages.lock.json': '{"consumer":"unchanged"}\n'}
            configuration = '.specify/extensions/program-kit-governance/program-kit-governance-config.yml'
            config_path = target / configuration
            self.assertTrue(config_path.is_file())
            authored[configuration] = config_path.read_text() + '\n# Consumer-owned configuration comment\n'
            for relative, text in authored.items():
                path = target / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            plan = updater.refresh(target, release, previous, plan_only=True)
            self.assertEqual('1.0.0-preview.2', plan['toVersion'])
            customized = target / '.specify/extensions/program-kit-governance/scripts/product_intake.py'
            original = customized.read_bytes()
            customized.write_bytes(original + b'\n# Consumer customization\n')
            with self.assertRaisesRegex(updater.UpgradeError, 'customized'):
                updater.refresh(target, release, previous, plan_only=True)
            self.assertTrue(customized.read_bytes().endswith(b'# Consumer customization\n'))
            customized.write_bytes(original)
            profiles = updater.load_module(release / 'extensions/program-kit-governance/scripts/render_profile.py', 'preview_test_profiles')
            records, _ = profiles.history(target)
            native_output = target / next(relative for row in records for relative in row['outputs']
                if 'program-kit-governance' in relative and relative.endswith('SKILL.md'))
            original_output = native_output.read_bytes()
            native_output.write_bytes(original_output + b'\nConsumer output customization\n')
            with self.assertRaisesRegex(updater.UpgradeError, 'customized'):
                updater.refresh(target, release, previous, plan_only=True)
            self.assertTrue(native_output.read_bytes().endswith(b'Consumer output customization\n'))
            native_output.write_bytes(original_output)
            # Device diagnostics are separately tested; this fixture exercises native refresh only.
            real_loader = updater.load_module
            def loader(path, name):
                if name == 'preview_devices':
                    return SimpleNamespace(contributor=lambda *args, **kwargs: None)
                return real_loader(path, name)
            # Fail after a real native component write; rollback retains both native and authored bytes.
            before = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            calls = []
            def failing_loader(path, name):
                module = loader(path, name)
                if name == 'preview_extension_copy':
                    install = module.install
                    def fail_after_first(*args, **kwargs):
                        calls.append(args[2])
                        if len(calls) == 2:
                            raise ValueError('Fictional second-component failure')
                        return install(*args, **kwargs)
                    module.install = fail_after_first
                return module
            with patch.object(updater, 'load_module', side_effect=failing_loader), self.assertRaisesRegex(ValueError, 'second-component'):
                updater.refresh(target, release, previous)
            self.assertEqual(before, {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()})
            with patch.object(updater, 'load_module', side_effect=loader):
                result = updater.refresh(target, release, previous)
            self.assertEqual('native-toolkit-refreshed', result['status'])
            self.assertEqual('1.0.0-preview.2', updater.manifest_version(target / '.specify/extensions/program-kit-governance/extension.yml'))
            for relative, text in authored.items():
                self.assertEqual(text, (target / relative).read_text())
            self.assertFalse((target / '.specify/governance/migration-completion.json').exists())


def native_refresh():
    suite = unittest.TestSuite([PreviewDistribution('test_native_preview_refresh_preserves_authored_work_and_refuses_customizations')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError('Native preview refresh/preservation failed')


if __name__ == '__main__':
    if '--native' in sys.argv:
        native_refresh()
    else:
        names = [name for name in unittest.defaultTestLoader.getTestCaseNames(PreviewDistribution) if not name.startswith('test_native_')]
        result = unittest.TextTestRunner().run(unittest.TestSuite(PreviewDistribution(name) for name in names))
        raise SystemExit(not result.wasSuccessful())
