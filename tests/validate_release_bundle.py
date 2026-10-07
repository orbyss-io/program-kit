"""Offline bundle production/admission and published-runtime boundary checks; no agent."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'
sys.path.insert(0, str(TEMPLATE / 'eng'))
import release_bundle as bundle
from live.v2.lending_host import unpack_release_bundle, PublishedLendingHost, LendingHost
from live.v2.common import LiveContractError


class ReleaseBundleTests(unittest.TestCase):
    def test_local_nuget_source_does_not_use_http_and_requires_exact_identity(self):
        feed = self.root / 'local-feed'
        feed.mkdir()
        package = feed / 'Example.Feature.1.2.3.nupkg'
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('Example.Feature.nuspec', '<package><metadata><id>Example.Feature</id><version>1.2.3</version></metadata></package>')
        destination = self.root / 'resolved.nupkg'
        with patch.object(bundle.urllib.request, 'urlopen', side_effect=AssertionError('Local source must not use HTTP')):
            bases = bundle.package_base_addresses([str(feed)])
            bundle.download_package('Example.Feature', '1.2.3', bases, destination)
            self.assertEqual(package.read_bytes(), destination.read_bytes())
            with self.assertRaises(FileNotFoundError):
                bundle.download_package('Example.Feature', '9.9.9', bases, destination)
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('Example.Feature.nuspec', '<package><metadata><id>Different</id><version>1.2.3</version></metadata></package>')
            with self.assertRaisesRegex(ValueError, 'differs from requested'):
                bundle.download_package('Example.Feature', '1.2.3', bases, destination)

    def test_installed_bundle_tool_includes_its_legacy_descriptor_bridge(self):
        with tempfile.TemporaryDirectory(prefix='installed-bundle-tool-') as directory:
            target = Path(directory)
            result = subprocess.run([sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                                     '--target', str(target), '--profile-selected', '--foundation-host-accepted',
                                     '--building-block-sources-approved', '--web-profile', 'none'], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            installed = target / 'eng/legacy-feature-bridge.json'
            self.assertEqual((TEMPLATE / 'eng/legacy-feature-bridge.json').read_bytes(), installed.read_bytes())
            result = subprocess.run([sys.executable, '-I', '-c',
                                     'import sys;sys.path.insert(0,sys.argv[1]);import release_bundle;'
                                     'assert release_bundle.LEGACY_FEATURE_BRIDGE["packageVersions"] == ["0.2.2","0.2.3"]',
                                     str(target / 'eng')], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='release-bundle-contract-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'artifacts/release-bundle'
        self.packages = self.root / 'artifacts/packages'
        self.packages.mkdir(parents=True)
        self.write('VERSION', '1.2.3\n')
        self.write('eng/application-handoff.json', {'schemaVersion': 1, 'applicationId': 'example.release'})
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

    def test_publisher_multi_feature_metadata_and_private_dependencies(self):
        package = self.packages / 'Publisher.1.0.0.nupkg'
        value = {'schemaVersion': 2, 'packageId': 'Publisher', 'features': [
            {'identity': name, 'featureDependencies': [], 'runtimeDependencies': [],
             'routes': ['/shared'] if name == 'One' else [], 'dormant': True}
            for name in ('One', 'Two')], 'hostProvidedDependencies': [
                {'packageId': 'Private.Runtime', 'minimumVersion': '1.2.3'}]}
        def pack(metadata, legacy=None):
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('Publisher.nuspec', '<package><metadata><id>Publisher</id><version>1.0.0</version></metadata></package>')
                archive.writestr('orbyss-foundation/feature.json', json.dumps(metadata))
                if legacy is not None: archive.writestr('program-kit/feature.json', json.dumps(legacy))
        pack(value)
        self.assertEqual([item['identity'] for item in bundle.package_features(package)], ['One', 'Two'])
        self.assertEqual(bundle.package_dependencies(package), {('Private.Runtime', '1.2.3')})
        self.write('shells.json', {'CShells': {'Shells': {'default': {'Features': {'One': {}, 'Two': {}}}}}})
        bundle.validate_feature_closure(self.root / 'shells.json', {('Publisher', '1.0.0'): package})
        value['features'][1]['routes'] = ['/shared']
        pack(value)
        with self.assertRaisesRegex(ValueError, 'PKR012'):
            bundle.validate_feature_closure(self.root / 'shells.json', {('Publisher', '1.0.0'): package})
        pack(value, dict(value, packageId='Spoof'))
        with self.assertRaisesRegex(ValueError, 'conflicting'): bundle.package_features(package)
        value['features'][1]['identity'] = 'One'
        pack(value)
        with self.assertRaisesRegex(ValueError, 'repeated'): bundle.package_features(package)

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
        dev = (ROOT/'extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/eng/Dev.ps1').read_text()
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
        migrated = dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', payload, migrations)
        expected = json.loads(payload)
        expected['contracts'][0]['packageClosure'] = 'artifacts/release-bundle/packages'
        self.assertEqual(json.loads(migrated), expected)
        self.assertEqual(dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', migrated, migrations), migrated)
        native = json.dumps({'schemaVersion': 1, 'contracts': ['contracts/openapi/api.contract.json']}).encode()
        self.assertEqual(native, dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', native, migrations))
        invalid = json.dumps({'contracts': [42]}).encode()
        with self.assertRaises(ValueError):
            dotnet_sync.apply_structured_migrations('eng/openapi-contracts.json', invalid, migrations)


if __name__ == '__main__': unittest.main()
