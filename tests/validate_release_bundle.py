"""Offline bundle production/admission and published-runtime boundary checks; no agent."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
sys.path.insert(0, str(TEMPLATE / '.program-kit/eng'))
import release_bundle as bundle
from live.v2.lending_host import unpack_release_bundle, PublishedLendingHost, LendingHost
from live.v2.common import LiveContractError


class ReleaseBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='release-bundle-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'artifacts/release-bundle'
        self.packages = self.root / 'artifacts/packages'
        self.packages.mkdir(parents=True)
        self.write('VERSION', '1.2.3\n')
        self.write('hostsettings.json', {})
        self.write('nuplane.settings.json', {'Nuplane': {'Setup': {'Feeds': []}, 'Loading': {'Enabled': True}}})
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {}}}}})
        self.write('NuGet.config', '<configuration><packageSources /></configuration>')
        self.write('Directory.Packages.props', '<Project/>')
        patcher = patch.dict(os.environ, {'GITHUB_SHA': 'a' * 40})
        patcher.start(); self.addCleanup(patcher.stop)
        self.image = 'ghcr.io/orbyss-io/foundation-host'
        self.digest = 'sha256:' + 'b' * 64
        self.descriptor = self.root / 'artifacts/application-bundle.json'

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding='utf-8')

    def produce(self):
        with patch.object(bundle, 'package_base_addresses', return_value=[]), patch.object(bundle, 'download_package', side_effect=AssertionError('unexpected feed access')):
            bundle.stage(self.root, self.packages, self.stage)
        bundle.describe(self.root, self.stage, self.image, 'v0.2.0', self.digest, self.descriptor)
        return self.descriptor.with_suffix('.zip')

    def test_configuration_only_bundle_runs_through_real_producer_and_admission(self):
        archive = self.produce()
        manifest = unpack_release_bundle(archive, self.root / 'admitted')
        self.assertEqual(manifest['application']['version'], '1.2.3')
        self.assertEqual(manifest['hostImage']['tag'], 'v0.2.0')
        self.assertEqual(manifest['runtimeClosure']['packageCount'], 0)
        self.assertEqual(json.loads((self.root/'admitted/hostsettings.json').read_text())['Nuplane'],
                         json.loads((self.root/'nuplane.settings.json').read_text())['Nuplane'])
        self.assertEqual((self.root/'hostsettings.json').read_text(), '{}')
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), archive.with_suffix('.zip.sha256').read_text().split()[0])

    def test_bundled_feed_package_is_hash_bound(self):
        with zipfile.ZipFile(self.packages/'Example.1.0.0.nupkg', 'w') as z:
            z.writestr('Example.nuspec', '<package><metadata><id>Example</id><version>1.0.0</version></metadata></package>')
        archive = self.produce()
        manifest = unpack_release_bundle(archive, self.root/'admitted')
        self.assertEqual(manifest['runtimeClosure']['packageCount'], 1)

    def test_same_inputs_produce_identical_archive(self):
        first = self.produce().read_bytes()
        self.assertEqual(first, self.produce().read_bytes())

    def test_conflicting_nuplane_authority_fails(self):
        self.write('hostsettings.json', {'Nuplane': {'Loading': {'Enabled': False}}})
        with self.assertRaisesRegex(ValueError, 'conflicting Nuplane'):
            self.produce()

    def test_missing_nuplane_is_not_silently_omitted(self):
        (self.root/'nuplane.settings.json').unlink()
        with self.assertRaises(FileNotFoundError): self.produce()

    def test_configuration_edit_requires_restaging_before_release(self):
        self.produce()
        self.write('nuplane.settings.json', {'Nuplane': {'Loading': {'Enabled': False}}})
        with self.assertRaisesRegex(ValueError, 'PKR022.*sourceConfiguration'):
            bundle.describe(self.root, self.stage, self.image, 'v0.2.0', self.digest, self.descriptor)

    def test_remote_feed_configuration_is_retained_without_claiming_activation(self):
        settings = {'Nuplane': {'Setup': {'Feeds': [{'Name': 'approved-feed', 'ServiceIndex': 'https://example.invalid/v3/index.json'}]}}}
        self.write('nuplane.settings.json', settings)
        self.produce()
        self.assertEqual(json.loads((self.stage/'nuplane.settings.json').read_text()), settings)
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'Unresolved': {}}}}}})
        with self.assertRaisesRegex(ValueError, 'PKR009'): self.produce()

    def test_consumer_image_is_rejected(self):
        self.image = 'ghcr.io/example/consumer'
        with self.assertRaisesRegex(ValueError, 'consumer images are forbidden'): self.produce()

    def test_modified_configuration_and_injected_host_binary_fail_admission(self):
        archive = self.produce()
        original = archive.read_bytes()
        for name, content in [('hostsettings.json', b'{}'), ('Orbyss.Foundation.Host.dll', b'fake'), ('../escape', b'bad')]:
            archive.write_bytes(original)
            with zipfile.ZipFile(archive) as z: files = {n:z.read(n) for n in z.namelist()}
            files[name] = content
            with zipfile.ZipFile(archive, 'w') as z:
                for n,v in files.items(): z.writestr(n,v)
            with self.assertRaises(LiveContractError): unpack_release_bundle(archive, self.root/'rejected')
            self.assertFalse((self.root/'rejected').exists())

    def test_runtime_mounts_individual_bundle_inputs_without_hiding_host(self):
        self.produce()
        host = PublishedLendingHost(self.stage, self.image+'@'+self.digest, self.root, self.root/'evidence', {})
        with patch.object(LendingHost, 'start', return_value=host): host.start()
        self.assertEqual(host.command[:2], ['docker','run'])
        self.assertEqual(host.command[-1], self.image+'@'+self.digest)
        self.assertNotIn('target=/app,', ' '.join(host.command))
        self.assertNotIn('build', host.command)
        self.assertIn('target=/app/hostsettings.json,readonly', ' '.join(host.command))

    def test_shipped_consumer_paths_cannot_publish_images(self):
        release = (TEMPLATE/'.github/workflows/application-release.yml').read_text()
        dev = (ROOT/'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/.program-kit/eng/Dev.ps1').read_text()
        for forbidden in ('docker build', 'docker push', 'buildx', 'packages: write'):
            self.assertNotIn(forbidden, release)
        self.assertNotIn('docker build', dev)
        self.assertFalse((TEMPLATE/'Dockerfile').exists())
        self.assertIn('application-bundle.zip', release)
        nuplane = json.loads((TEMPLATE/'nuplane.settings.json').read_text())
        self.assertEqual(nuplane['Nuplane']['Setup']['Feeds'][0]['IncludePatterns'], ['*'],
                         'Validated consumer packages must not be excluded by an Orbyss-only filter')

    def test_upgrade_moves_only_the_old_managed_closure_reference(self):
        sys.path.insert(0, str(ROOT/'extensions/program-kit-dotnet/scripts'))
        import dotnet_sync
        migrations = json.loads((ROOT/'extensions/program-kit-dotnet/templates/dotnet/migrations.json').read_text())['migrations']
        original = {'schemaVersion': 1, 'owner': 'consumer', 'contracts': [
            {'id':'api', 'packageClosure':'artifacts/runnable-host/packages', 'baseline':'contracts/v1.json'},
            {'id':'custom', 'packageClosure':'consumer/special', 'baseline':'contracts/other.json'}]}
        payload = json.dumps(original).encode()
        migrated = dotnet_sync.apply_structured_migrations('.program-kit/openapi-contracts.json', payload, migrations)
        expected = json.loads(payload)
        expected['contracts'][0]['packageClosure'] = 'artifacts/release-bundle/packages'
        self.assertEqual(json.loads(migrated), expected)
        self.assertEqual(dotnet_sync.apply_structured_migrations('.program-kit/openapi-contracts.json', migrated, migrations), migrated)


if __name__ == '__main__': unittest.main()
