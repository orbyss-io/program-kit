"""HostedPages public bytes must participate in native bundle freshness/inventory."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
import runtime_closure
import release_bundle
import hosted_bundle


class HostedBundleContentTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / 'artifacts/cache/hosted-bundle-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'packages').mkdir()
        self.asset = self.root / 'web/dist/application.js'
        self.asset.parent.mkdir(parents=True)
        self.asset.write_bytes(b'export async function mount() {}')
        manifest = {'version': '1', 'currentRevision': 'one', 'revisions': [{
            'id': 'one', 'assets': [{'file': 'application.js', 'visibility': 'public',
                                   'sha256': hashlib.sha256(self.asset.read_bytes()).hexdigest()}]}]}
        self.manifest = self.root / 'web/dist/manifest.json'
        self.manifest.write_text(json.dumps(manifest), encoding='utf-8')
        self.settings = {'CShells': {'Shells': {'default': {
            'Features': {'Orbyss.Foundation.Web.HostedPages': {}},
            'Configuration': {'Foundation': {'HostedPages': {
                'Root': 'web/dist', 'Manifest': 'manifest.json', 'CurrentRevision': 'one',
                'ManifestSha256': hashlib.sha256(self.manifest.read_bytes()).hexdigest()}}}}}}}
        self.write_settings()
        for name in ('hostsettings.json', 'nuplane.settings.json'):
            (self.root / name).write_text('{}', encoding='utf-8')

    def write_settings(self):
        (self.root / 'shells.json').write_text(json.dumps(self.settings), encoding='utf-8')

    def test_native_closure_includes_manifest_and_admitted_assets_only(self):
        (self.asset.parent / 'private.txt').write_text('unlisted sentinel', encoding='utf-8')
        inventory = runtime_closure.write_value(self.root, self.root, '0.13.0')
        self.assertEqual({'web/dist/manifest.json', 'web/dist/application.js'},
                         {item['file'] for item in inventory.get('content', [])})

    def test_changed_asset_cannot_seal_current_manifest(self):
        self.asset.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            runtime_closure.write_value(self.root, self.root, '0.13.0')

    def test_native_mount_keeps_admitted_content_beneath_its_frontend_directory(self):
        self.assertEqual(['web'], hosted_bundle.public_mount_roots(self.root, self.settings))

    def test_native_mount_rejects_unlisted_sibling_bytes(self):
        (self.root / 'web/private.txt').write_text('unlisted private sibling', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'unlisted bytes'):
            hosted_bundle.public_mount_roots(self.root, self.settings)

    def test_manifest_hash_mismatch_rejects(self):
        self.manifest.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            runtime_closure.write_value(self.root, self.root, '0.13.0')

    def test_private_asset_never_enters_public_bundle_inventory(self):
        manifest = json.loads(self.manifest.read_text())
        manifest['revisions'][0]['assets'][0]['visibility'] = 'private'
        self.manifest.write_text(json.dumps(manifest), encoding='utf-8')
        self.settings['CShells']['Shells']['default']['Configuration']['Foundation']['HostedPages']['ManifestSha256'] = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.write_settings()
        with self.assertRaises(ValueError):
            runtime_closure.write_value(self.root, self.root, '0.13.0')

    def test_source_freshness_contains_compiled_snapshot(self):
        self.assertIn('web/dist/application.js', {item['file'] for item in runtime_closure.source_configuration(self.root)})

    def test_archive_contains_admitted_bytes_and_excludes_unlisted_content(self):
        (self.root / 'VERSION').write_text('0.1.0', encoding='utf-8')
        (self.asset.parent / 'private.txt').write_text('unlisted sentinel', encoding='utf-8')
        evidence = self.root / 'artifacts/closure.json'
        runtime_closure.write_success(self.root, self.root, evidence, release_bundle.PROGRAM_KIT_VERSION)
        output = self.root / 'artifacts/application-bundle.json'
        with patch.object(release_bundle, 'application_identity', return_value='synthetic-bundle-test'), patch.object(release_bundle, 'source_commit', return_value='1' * 40):
            release_bundle.describe(self.root, self.root, 'ghcr.io/orbyss-io/foundation-host', '0.3.3',
                                    'sha256:' + '1' * 64, output, evidence)
        with zipfile.ZipFile(output.with_suffix('.zip')) as archive:
            self.assertIn('web/dist/manifest.json', archive.namelist())
            self.assertEqual(self.asset.read_bytes(), archive.read('web/dist/application.js'))
            self.assertNotIn('web/dist/private.txt', archive.namelist())

    def test_asset_traversal_rejects_before_copy(self):
        manifest = json.loads(self.manifest.read_text())
        manifest['revisions'][0]['assets'][0]['file'] = '../private.txt'
        self.manifest.write_text(json.dumps(manifest), encoding='utf-8')
        self.settings['CShells']['Shells']['default']['Configuration']['Foundation']['HostedPages']['ManifestSha256'] = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.write_settings()
        with self.assertRaises(ValueError):
            runtime_closure.write_value(self.root, self.root, '0.13.0')

    def test_source_change_during_stage_cannot_be_sealed_as_current(self):
        staged = self.root / 'artifacts/staged'
        staged.mkdir(parents=True)
        for name in ('shells.json', 'hostsettings.json', 'nuplane.settings.json'):
            shutil.copyfile(self.root / name, staged / name)
        shutil.copytree(self.root / 'web', staged / 'web')
        self.settings['CShells']['Shells']['default']['Configuration']['changed'] = True
        self.write_settings()
        with self.assertRaises(ValueError):
            runtime_closure.write_value(self.root, staged, '0.13.0')


if __name__ == '__main__':
    unittest.main()
