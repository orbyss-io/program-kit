"""Development overlays bind exact private F6 artifacts and never qualify a public default."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_foundation_contracts_development_profile as candidate


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


class DevelopmentProfileTests(unittest.TestCase):
    def setUp(self):
        # Synthetic unit-test evidence exercises preparation guards; it is never F6 acceptance.
        self.temp = tempfile.TemporaryDirectory(prefix='pk2a-negative-', dir=ROOT / 'artifacts')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feed = self.root / 'feed'
        self.feed.mkdir()
        self.f6 = self.root / 'f6'
        self.f6.mkdir()
        self.host = self.root / 'Orbyss.Foundation.Host.dll'
        self.host.write_bytes(b'unit-test-private-host')
        for name in ('Orbyss.Foundation.Host.deps.json', 'Orbyss.Foundation.Host.runtimeconfig.json', 'appsettings.json'):
            (self.root / name).write_text('{}', encoding='utf-8')
        (self.root / 'Nuplane.Loading.dll').write_bytes(b'unit-test-native-loader')
        self.native = self.root / 'runtimes/win-x64/native/fixture-native.dll'
        self.native.parent.mkdir(parents=True)
        self.native.write_bytes(b'unit-test-native-runtime-asset')
        recipe = candidate.recipe()
        self.identity = recipe['profileId']
        self.version = recipe['foundationVersion']
        catalog = candidate.base_catalog()[0]
        identities = {package['packageId'] for package in catalog['packages'].values()
                      if package['family'] == 'foundation' and package['materialization']['kind'] == 'nuget-project'}
        identities.update(recipe['supplementalRuntimePackages'])
        for identity in sorted(identities):
            self.package(identity, self.version)
        self.package('Orbyss.Foundation.Build', '0.1.0')
        self.inputs = {'version': self.version, 'host': {'path': str(self.host), 'sha256': candidate.digest(self.host)},
            'hostRuntimeFiles': candidate.host_runtime_inventory(self.host),
            'packages': {path.name: candidate.digest(path) for path in self.feed.glob('*.nupkg')},
            'candidatePackageIdentities': sorted(identities), 'sourceProjectReferences': False,
            'postgresql': 'synthetic unit-test evidence only'}
        self.result = {'status': 'passed', 'version': self.version, 'actualHost': True,
            'actualNugetPackages': True, 'actualPostgreSql': True, 'twoShells': True,
            'historicalEvidencePreserved': True}
        write(self.f6 / 'inputs.json', self.inputs)
        write(self.f6 / 'result.json', self.result)
        self.output = self.root / 'profile'

    def package(self, identity, version):
        with zipfile.ZipFile(self.feed / (identity + '.' + version + '.nupkg'), 'w') as archive:
            archive.writestr(identity + '.nuspec', f'<package><metadata><id>{identity}</id><version>{version}</version></metadata></package>')

    def prepare(self):
        return candidate.prepare(self.identity, self.version, self.f6 / 'result.json', self.feed, self.host, self.output)

    def test_exact_overlay_and_pins_retain_composition_and_public_defaults(self):
        before = {path: path.read_bytes() for path in candidate.public_sources()}
        self.prepare()
        record = candidate.verify(self.output, self.identity, f6_result=self.f6 / 'result.json', packages=self.feed, host=self.host)
        self.assertIs(False, record['publicAvailabilityEstablished'])
        self.assertIs(False, record['defaultPromotionPerformed'])
        index = json.loads((self.output / 'index.json').read_text())
        self.assertIsNone(index['default'])
        overlay = json.loads((self.output / 'catalog.json').read_text())
        baseline, _ = candidate.base_catalog()
        self.assertEqual(candidate.blocks.composition_projection(baseline), candidate.blocks.composition_projection(overlay))
        self.assertEqual(before, {path: path.read_bytes() for path in before})
        for key, package in overlay['packages'].items():
            if package['family'] == 'foundation' and package['materialization']['kind'] == 'nuget-project':
                self.assertEqual(self.version, package['version'])
            else:
                self.assertEqual(baseline['packages'][key]['version'], package['version'])
        with self.assertRaises(candidate.blocks.ResolverError):
            candidate.blocks.qualified_dependency_profile(self.output, self.identity, baseline)
        self.assertEqual(record, self.prepare())

    def test_f6_failed_malformed_version_and_project_reference_evidence_rejected(self):
        for mutate in (lambda value: value.update(status='failed'), lambda value: value.update(actualHost=False),
                       lambda value: value.update(actualPostgreSql=False), lambda value: value.update(twoShells=False),
                       lambda value: value.update(version='0.2.4')):
            changed = copy.deepcopy(self.result)
            mutate(changed)
            write(self.f6 / 'result.json', changed)
            with self.subTest(change=changed), self.assertRaises(ValueError): self.prepare()
        write(self.f6 / 'result.json', self.result)
        for mutate in (lambda value: value.update(sourceProjectReferences=True), lambda value: value['packages'].clear(),
                       lambda value: value['host'].update(sha256='not-a-hash'), lambda value: value['candidatePackageIdentities'].pop()):
            changed = copy.deepcopy(self.inputs)
            mutate(changed)
            write(self.f6 / 'inputs.json', changed)
            with self.subTest(change=changed), self.assertRaises(ValueError): self.prepare()
        (self.f6 / 'inputs.json').write_text('{not json', encoding='utf-8')
        with self.assertRaises(ValueError): self.prepare()

    def test_changed_feed_host_and_mixed_candidate_versions_rejected(self):
        self.prepare()
        self.host.write_bytes(b'changed-host')
        with self.assertRaises(ValueError): candidate.verify(self.output, self.identity)
        self.host.write_bytes(b'unit-test-private-host')
        package = next(self.feed.glob('*.nupkg'))
        original = package.read_bytes()
        package.write_bytes(original + b'changed-input')
        with self.assertRaises(ValueError): candidate.verify(self.output, self.identity)
        package.write_bytes(original)
        self.package('Orbyss.Foundation.Json', '0.2.4')
        with self.assertRaises(ValueError): self.prepare()

    def test_host_dependencies_and_configuration_cannot_change_behind_the_same_host_dll(self):
        self.prepare()
        for name in ('Nuplane.Loading.dll', 'appsettings.json', 'Orbyss.Foundation.Host.deps.json', 'Orbyss.Foundation.Host.runtimeconfig.json',
                     self.native.relative_to(self.root).as_posix()):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b'changed')
            with self.subTest(file=name), self.assertRaisesRegex(ValueError, 'dependency/configuration'):
                candidate.verify(self.output, self.identity)
            path.write_bytes(original)
        missing = self.root / 'Orbyss.Foundation.Host.runtimeconfig.json'
        original = missing.read_bytes()
        missing.unlink()
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            candidate.verify(self.output, self.identity)
        missing.write_bytes(original)
        (self.root / 'new-native-dependency.dll').write_bytes(b'added')
        with self.assertRaisesRegex(ValueError, 'dependency/configuration'):
            candidate.verify(self.output, self.identity)

    def test_self_consistent_but_incomplete_or_mixed_feed_is_not_a_runtime_profile(self):
        for package, version in (('Orbyss.Foundation.Json', '0.2.4'), ('Orbyss.Foundation.Execution.Core', None)):
            path = self.feed / (package + '.' + self.version + '.nupkg')
            original = path.read_bytes()
            path.unlink()
            if version:
                self.package(package, version)
            changed = copy.deepcopy(self.inputs)
            changed['packages'] = {entry.name: candidate.digest(entry) for entry in self.feed.glob('*.nupkg')}
            changed['candidatePackageIdentities'].remove(package)
            write(self.f6 / 'inputs.json', changed)
            with self.subTest(package=package), self.assertRaises(ValueError): self.prepare()
            if version:
                (self.feed / (package + '.' + version + '.nupkg')).unlink()
            path.write_bytes(original)
        write(self.f6 / 'inputs.json', self.inputs)

    def test_external_dependency_versions_retain_exact_f6_hashes(self):
        self.package('External.Fixture', '1.0.0')
        self.package('External.Fixture', '2.0.0')
        self.inputs['packages'] = {entry.name: candidate.digest(entry) for entry in self.feed.glob('*.nupkg')}
        write(self.f6 / 'inputs.json', self.inputs)
        self.prepare()
        candidate.verify(self.output, self.identity)
        self.package('orbyss.foundation.Json', self.version)
        self.inputs['packages'] = {entry.name: candidate.digest(entry) for entry in self.feed.glob('*.nupkg')}
        write(self.f6 / 'inputs.json', self.inputs)
        with self.assertRaisesRegex(ValueError, 'noncanonical casing'): self.prepare()

    def test_identity_membership_is_exact_independent_of_platform_path_sorting(self):
        self.inputs['candidatePackageIdentities'].reverse()
        write(self.f6 / 'inputs.json', self.inputs)
        self.prepare()
        candidate.verify(self.output, self.identity)
        self.inputs['candidatePackageIdentities'].append(self.inputs['candidatePackageIdentities'][0])
        write(self.f6 / 'inputs.json', self.inputs)
        with self.assertRaisesRegex(ValueError, 'candidate package identities'): self.prepare()

    def test_implicit_selection_and_public_promotion_claims_rejected(self):
        self.prepare()
        for identity in (None, '', 'default', self.identity + '-other'):
            with self.subTest(identity=identity), self.assertRaises(ValueError): candidate.verify(self.output, identity)
        index_path = self.output / 'index.json'
        original = json.loads(index_path.read_text())
        for mutate in (lambda value: value.update(default=self.identity), lambda value: value.update(publicAvailabilityEstablished=True),
                       lambda value: value['profiles'][self.identity].update(status='qualified')):
            changed = copy.deepcopy(original)
            mutate(changed)
            write(index_path, changed)
            with self.assertRaises(ValueError): candidate.verify(self.output, self.identity)
        write(index_path, original)
        evidence = self.output / 'evidence.json'
        changed = json.loads(evidence.read_text())
        changed['publicHostAvailabilityEstablished'] = True
        write(evidence, changed)
        with self.assertRaises(ValueError): candidate.verify(self.output, self.identity)

    def test_preserved_output_rejects_stale_pins_and_other_named_recipe(self):
        self.prepare()
        pins = self.output / 'runtime-packages.props'
        pins.write_text(pins.read_text().replace(self.version, '0.2.4'))
        with self.assertRaises(ValueError): candidate.verify(self.output, self.identity)
        with self.assertRaises(ValueError): self.prepare()
        with self.assertRaises(ValueError): candidate.prepare(self.identity, '0.2.4', self.f6 / 'result.json', self.feed, self.host, self.output)
        with self.assertRaises(ValueError): candidate.prepare(self.identity, self.version, self.f6 / 'result.json', self.feed, self.host, candidate.blocks.profile_registry())


if __name__ == '__main__':
    unittest.main()
