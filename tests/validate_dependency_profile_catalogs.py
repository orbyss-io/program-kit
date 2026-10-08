"""Profile-bound additive catalogs retain historical rules and exact qualification guards.

All new registry entries in this validator are isolated synthetic unit fixtures. They
establish no package availability, published profile or public default authority.
"""
from __future__ import annotations

import copy
import io
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import building_blocks as blocks
import dependency_profiles as profiles
import profile_catalogs as catalogs
import validate_building_blocks as fixtures
import json_schema

IDENTITY = 'synthetic-additive-contracts-profile'
CORE = 'nuget:Orbyss.Foundation.Authentication.Core'
AUTH = 'nuget:Orbyss.Foundation.Authentication'


class GeneratedEngineeringPinsTests(unittest.TestCase):
    def setUp(self):
        source = ROOT / 'extensions/program-kit-dotnet/scripts/dependency_profile.py'
        spec = importlib.util.spec_from_file_location('catalog_pin_renderer', source)
        self.renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.renderer)
        registry = blocks.profile_registry() / 'catalogs/foundation-0-3-0-contracts'
        self.target = blocks.load_json(next(registry.glob('target-*.json')))
        self.base = blocks.load_json(blocks.default_catalog(Path(blocks.__file__)))
        self.content = (ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng/ProgramKit.Packages.props').read_bytes()

    def render(self, catalog, content=None, relative='eng/ProgramKit.Packages.props'):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection, _ = fixtures.accepted_fixture(blocks, root, catalog)
            source = root / 'captured-catalog.json'
            fixtures.write_json(source, catalog)
            blocks.preserve_dependency_profile(root, blocks.load_json(selection), source)
            return self.renderer.render(root, relative, self.content if content is None else content)

    def test_selected_catalog_generates_independent_build_and_analyzer_pins(self):
        original = copy.deepcopy(self.target)
        generated = ET.fromstring(self.render(self.target))
        pins = {node.attrib['Include']: node.attrib['Version'] for node in generated.iter('PackageVersion')}
        self.assertEqual('0.2.0', pins['Orbyss.Foundation.Build'])
        self.assertEqual('0.3.0', pins['Orbyss.Foundation.Analyzers'])
        self.assertEqual(self.target, original)
        retained = self.render(self.target, b'{}', 'eng/building-blocks.catalog.json')
        self.assertEqual(self.target, json.loads(retained))

    def test_missing_or_duplicate_selected_build_pin_rejects_managed_rendering(self):
        import re
        line=re.search(rb'[^\n]*<PackageVersion Include="Orbyss.Foundation.Build" Version="[^"]+" />',self.content)[0]
        self.assertEqual(1, self.content.count(line))
        for content in (self.content.replace(line, b''), self.content.replace(line, line + b'\n' + line)):
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, 'builder pin.*exactly once'):
                self.render(self.target, content)

    def test_historical_catalog_preserves_unregistered_build_pin_and_unrelated_content(self):
        self.assertNotIn('nuget:Orbyss.Foundation.Build', self.base['packages'])
        generated = ET.fromstring(self.render(self.base))
        pins = {node.attrib['Include']: node.attrib['Version'] for node in generated.iter('PackageVersion')}
        original_builder=next(node.attrib['Version'] for node in ET.fromstring(self.content).iter('PackageVersion')
                              if node.attrib['Include']=='Orbyss.Foundation.Build')
        self.assertEqual(original_builder, pins['Orbyss.Foundation.Build'])
        shared = blocks.load_json(blocks.profile_registry()/'engineering-contracts.json')['releases'][self.base['families']['foundation']['releaseVersion']]['pins']
        for identity, version in shared.items(): self.assertEqual(version, pins[identity])
        for identity, version in pins.items():
            if identity != 'Orbyss.Foundation.Analyzers' and identity not in shared:
                original = next(node.attrib['Version'] for node in ET.fromstring(self.content).iter('PackageVersion')
                                if node.attrib['Include'] == identity)
                self.assertEqual(original, version)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures.write_json(root / '.program-kit/managed.json', {})
            self.assertEqual(self.content, self.renderer.render(root, 'eng/ProgramKit.Packages.props', self.content))


class OfficialToolBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        import validate_default_dependency_profile as native
        self.native = native

    def test_qualifier_selects_actual_build_pin_before_pack_and_isolates_cli_state(self):
        base = blocks.load_json(blocks.default_catalog(Path(blocks.__file__)))
        selected = blocks.dependency_profile_value(base, 'synthetic-official-tools')
        selected['artifacts']['nuget:Orbyss.Foundation.Build'] = '0.2.0'
        profile = self.root / 'profile.json'
        fixtures.write_json(profile, selected)
        lock = self.root / 'native.lock.json'
        lock.write_text('{}')
        work = self.root / 'work'
        class RestoreObserved(Exception):
            pass
        def dispatch(arguments, **kwargs):
            self.assertIn('--locked-mode', arguments)
            central = ET.parse(work / 'eng/ProgramKit.Packages.props')
            actual = [node.attrib['Version'] for node in central.iter('PackageVersion')
                      if node.attrib.get('Include') == 'Orbyss.Foundation.Build']
            self.assertEqual(['0.2.0'], actual)
            self.assertEqual(str(work / 'dotnet-home'), kwargs['env'].get('DOTNET_CLI_HOME'))
            raise RestoreObserved()
        with patch.object(self.native.profile_catalogs, 'qualification_inputs', return_value={'catalog': base, 'nativeLock': lock}), \
                patch.object(self.native.subprocess, 'run', side_effect=dispatch):
            with self.assertRaises(RestoreObserved):
                self.native.qualify(profile, work, catalog_path=self.root / 'catalog.json', native_lock=lock,
                                    qualification_recipe=self.root / 'recipe.json')

    def package(self, identity='Orbyss.Foundation.Build', version='0.2.0'):
        package = self.root / 'cache' / identity.lower() / version / (identity.lower() + '.' + version + '.nupkg')
        package.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('tool.nuspec', '<package><metadata><id>' + identity + '</id><version>' + version + '</version></metadata></package>')
        fixtures.write_json(package.parent / '.nupkg.metadata', {'source': self.native.PUBLIC_SOURCE})
        return package

    def test_official_archive_binding_accepts_omitted_native_source_without_inventing_it(self):
        package = self.package()
        fixtures.write_json(package.parent / '.nupkg.metadata', {})
        with patch.object(self.native.urllib.request, 'urlopen', return_value=io.BytesIO(package.read_bytes())):
            binding = self.native.official_tool_binary(self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0', self.root / 'official')
        self.assertEqual(blocks.raw_sha256(package), binding['sha256'])
        self.assertIsNone(binding['nativeSource'])
        self.assertEqual(self.native.PUBLIC_SOURCE, binding['source'])
        self.assertIn('/orbyss.foundation.build/0.2.0/', binding['archiveUrl'])

    def test_nonpublic_wrong_identity_missing_provenance_and_changed_public_bytes_fail(self):
        package = self.package()
        official = package.read_bytes()
        proof = package.parent / '.nupkg.metadata'
        for provenance in ({'source': 'file:///private-feed'}, None):
            if provenance is None:
                proof.unlink()
            else:
                fixtures.write_json(proof, provenance)
            with patch.object(self.native.urllib.request, 'urlopen', return_value=io.BytesIO(official)):
                with self.assertRaises(ValueError):
                    self.native.official_tool_binary(self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0', self.root / 'official')
        fixtures.write_json(proof, {})
        with patch.object(self.native.urllib.request, 'urlopen', return_value=io.BytesIO(official + b'changed')):
            with self.assertRaisesRegex(ValueError, 'official'):
                self.native.official_tool_binary(self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0', self.root / 'official')
        with zipfile.ZipFile(package, 'w') as archive:
            archive.writestr('tool.nuspec', '<package><metadata><id>Impostor</id><version>0.2.0</version></metadata></package>')
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.native.official_tool_binary(self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0', self.root / 'official')

    def test_public_tool_configuration_and_resolved_build_admission_are_exact(self):
        config = self.root / 'NuGet.config'
        self.native.public_tool_configuration(config)
        sources = ET.parse(config).getroot().find('packageSources')
        self.assertEqual([('nuget.org', self.native.PUBLIC_SOURCE)], [(node.get('key'), node.get('value')) for node in sources.findall('add')])
        assets = self.root / 'assets.json'
        value = {'libraries': {'Orbyss.Foundation.Build/0.2.0': {'type': 'package'}},
                 'packageFolders': {str(self.root / 'cache'): {}}}
        fixtures.write_json(assets, value)
        self.native.require_resolved_tool(assets, self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0')
        for mutate in (lambda item: item['libraries'].update({'Orbyss.Foundation.Build/0.1.0': {'type': 'package'}}),
                       lambda item: item['libraries']['Orbyss.Foundation.Build/0.2.0'].update(type='project'),
                       lambda item: item['packageFolders'].update({str(self.root / 'ambient-cache'): {}})):
            invalid = copy.deepcopy(value)
            mutate(invalid)
            fixtures.write_json(assets, invalid)
            with self.assertRaises(ValueError):
                self.native.require_resolved_tool(assets, self.root / 'cache', 'Orbyss.Foundation.Build', '0.2.0')

    def test_named_official_tool_proof_rejects_missing_changed_versions_sources_and_hashes(self):
        selected = {'artifacts': {'nuget:Orbyss.Foundation.Build': '0.2.0',
                                  'nuget:Orbyss.Foundation.OpenApi.Exporter': '0.2.4'}}
        tools = {}
        for identity, version in ((self.native.BUILD, '0.2.0'), (self.native.TOOL, '0.2.4')):
            package = self.package(identity, version)
            with patch.object(self.native.urllib.request, 'urlopen', return_value=io.BytesIO(package.read_bytes())):
                tools[identity] = self.native.official_tool_binary(self.root / 'cache', identity, version, self.root / 'official')
        proof = self.root / 'official-tools.json'
        self.native.write(proof, tools)
        source = {'officialTools': tools, 'officialToolsSha256': blocks.raw_sha256(proof)}
        self.assertEqual(tools, blocks.named_official_tool_bindings(source, selected))
        for mutate in (lambda value: value.pop('officialTools'),
                       lambda value: value['officialTools'].pop(self.native.BUILD),
                       lambda value: value['officialTools'][self.native.BUILD].update(version='0.1.0'),
                       lambda value: value['officialTools'][self.native.TOOL].update(source='file:///source-built-tool'),
                       lambda value: value['officialTools'][self.native.TOOL].update(nativeSource='file:///private'),
                       lambda value: value['officialTools'][self.native.TOOL].update(archiveUrl='https://untrusted.invalid/tool.nupkg'),
                       lambda value: value['officialTools'][self.native.TOOL].update(sha256='changed'),
                       lambda value: value.update(officialToolsSha256='0' * 64)):
            changed = copy.deepcopy(source)
            mutate(changed)
            with self.assertRaises(blocks.ResolverError):
                blocks.named_official_tool_bindings(changed, selected)

    def test_sealer_rechecks_retained_official_restored_archives_and_native_provenance(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build_dependency_qualification import verify_official_tool_evidence
        selected, tools = {'artifacts': {}}, {}
        paths = []
        for identity, version in ((self.native.BUILD, '0.2.0'), (self.native.TOOL, '0.2.4')):
            package = self.package(identity, version)
            cache = self.root / 'cache'
            if identity == self.native.TOOL:
                destination = self.root / 'tool-cache' / package.relative_to(cache)
                destination.parent.mkdir(parents=True)
                shutil.copy2(package, destination)
                shutil.copy2(package.parent / '.nupkg.metadata', destination.parent / '.nupkg.metadata')
                package, cache = destination, self.root / 'tool-cache'
            with patch.object(self.native.urllib.request, 'urlopen', return_value=io.BytesIO(package.read_bytes())):
                tools[identity] = self.native.official_tool_binary(cache, identity, version, self.root / 'official-archives')
            selected['artifacts']['nuget:' + identity] = version
            paths += [package, package.parent / '.nupkg.metadata', self.root / 'official-archives' / package.name]
        proof = self.root / 'official-tools.json'
        self.native.write(proof, tools)
        source = {'officialTools': tools, 'officialToolsSha256': blocks.raw_sha256(proof)}
        verify_official_tool_evidence(self.root, source, selected)
        for path in [proof, *paths]:
            original = path.read_bytes()
            for changed in (True, False):
                if changed:
                    path.write_bytes(original + b'changed')
                else:
                    path.unlink()
                with self.assertRaises(ValueError):
                    verify_official_tool_evidence(self.root, source, selected)
                path.write_bytes(original)

    def test_named_runtime_closure_admits_inert_core_and_provider_and_rejects_missing_archives(self):
        catalog = {'packages': {}}
        closure = self.root / 'closure'
        closure.mkdir()
        artifacts = {}
        for identity in ('Orbyss.Foundation.Authentication.Core', 'Orbyss.Foundation.PostgreSql', self.native.BUILD):
            package = {'packageId': identity, 'ecosystem': 'nuget', 'version': '0.3.0',
                       'materialization': {'kind': 'nuget-project'}, 'activations': []}
            catalog['packages']['nuget:' + identity] = package
            if identity != self.native.BUILD:
                archive = closure / (identity + '.0.3.0.nupkg')
                with zipfile.ZipFile(archive, 'w') as value:
                    value.writestr('component.nuspec', '<package><metadata><id>' + identity + '</id><version>0.3.0</version></metadata></package>')
                artifacts[identity] = {'version': '0.3.0', 'sha256': blocks.raw_sha256(archive)}
        self.assertEqual({}, self.native.selected_runtime_packages(catalog, False))
        runtime = self.native.selected_runtime_packages(catalog, True)
        self.assertEqual(set(artifacts), {package['packageId'] for package in runtime.values()})
        self.native.require_selected_runtime_closure(runtime, artifacts, closure)
        for path in closure.glob('*.nupkg'):
            content = path.read_bytes()
            path.unlink()
            with self.assertRaisesRegex(ValueError, 'missing'):
                self.native.require_selected_runtime_closure(runtime, artifacts, closure)
            path.write_bytes(content + b'changed')
            with self.assertRaises(ValueError):
                self.native.require_selected_runtime_closure(runtime, artifacts, closure)
            path.write_bytes(content)

    def test_named_sealer_rejects_omitted_changed_inert_archives_and_publisher_disagreement(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build_dependency_qualification import verify_named_runtime_evidence
        catalog = {'packages': {}}
        closure = self.root / 'closure'
        closure.mkdir()
        artifacts = {}
        for identity in ('Orbyss.Foundation.Collections.Core', 'Orbyss.Foundation.PostgreSql'):
            catalog['packages']['nuget:' + identity] = {'packageId': identity, 'ecosystem': 'nuget', 'version': '0.3.0',
                                                       'materialization': {'kind': 'nuget-project'}, 'activations': []}
            path = closure / (identity + '.0.3.0.nupkg')
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('component.nuspec', '<package><metadata><id>' + identity + '</id><version>0.3.0</version></metadata></package>')
            artifacts[identity] = {'version': '0.3.0', 'sha256': blocks.raw_sha256(path)}
        publisher = self.root / 'publisher-metadata.json'
        fixtures.write_json(publisher, {'artifacts': artifacts, 'descriptors': {}})
        receipt = {'artifacts': copy.deepcopy(artifacts)}
        verify_named_runtime_evidence(self.root, catalog, receipt)
        for identity in artifacts:
            original = receipt['artifacts'].pop(identity)
            with self.assertRaisesRegex(ValueError, 'missing'):
                verify_named_runtime_evidence(self.root, catalog, receipt)
            receipt['artifacts'][identity] = original
            path = closure / (identity + '.0.3.0.nupkg')
            content = path.read_bytes()
            path.unlink()
            with self.assertRaises(ValueError):
                verify_named_runtime_evidence(self.root, catalog, receipt)
            path.write_bytes(content + b'changed')
            with self.assertRaises(ValueError):
                verify_named_runtime_evidence(self.root, catalog, receipt)
            # A self-consistent changed metadata/receipt pair still must match actual retained archives.
            receipt['artifacts'][identity]['sha256'] = '0' * 64
            fixtures.write_json(publisher, {'artifacts': receipt['artifacts'], 'descriptors': {}})
            with self.assertRaises(ValueError):
                verify_named_runtime_evidence(self.root, catalog, receipt)
            receipt['artifacts'][identity]['sha256'] = artifacts[identity]['sha256']
            path.write_bytes(content)
            changed = copy.deepcopy(artifacts)
            changed[identity]['sha256'] = '0' * 64
            fixtures.write_json(publisher, {'artifacts': changed, 'descriptors': {}})
            with self.assertRaisesRegex(ValueError, 'publisher artifacts'):
                verify_named_runtime_evidence(self.root, catalog, receipt)
            fixtures.write_json(publisher, {'artifacts': artifacts, 'descriptors': {}})

    def preparation_inputs(self):
        registry = blocks.profile_registry()
        profile = self.root / 'profile.json'
        catalog = self.root / 'catalog.json'
        shutil.copy2(registry / 'dependency-profile-foundation-0.3.0.json', profile)
        shutil.copy2(next((registry / 'catalogs/foundation-0-3-0-contracts').glob('target-*.json')), catalog)
        return profile, catalog

    def test_lock_preparation_uses_same_probe_and_only_ordinary_restore_without_qualification(self):
        profile, catalog = self.preparation_inputs()
        output = self.root / 'new-locks/contracts.json'
        work = self.root / 'preparation'
        selected = blocks.load_json(profile)
        runtime = self.native.selected_runtime_packages(blocks.load_json(catalog), True)
        observed = {'version': 2, 'dependencies': {'net10.0': {
            package['packageId']: {'type': 'Direct', 'resolved': package['version']} for package in runtime.values()}}}
        for identity in (self.native.BUILD, 'Orbyss.Foundation.Analyzers'):
            observed['dependencies']['net10.0'][identity] = {'type': 'Direct', 'resolved': selected['artifacts']['nuget:' + identity]}
        calls = []
        def dispatch(arguments, **kwargs):
            calls.append(arguments)
            self.assertEqual(['dotnet', 'restore'], arguments[:2])
            self.assertNotIn('--locked-mode', arguments)
            self.assertEqual(str(work / 'cache'), kwargs['env']['NUGET_PACKAGES'])
            self.assertEqual(str(work / 'dotnet-home'), kwargs['env']['DOTNET_CLI_HOME'])
            fixtures.write_json(work / 'Feature/packages.lock.json', observed)
            return subprocess.CompletedProcess(arguments, 0, 'synthetic ordinary restore\n', '')
        with patch.object(self.native, 'ROOT', self.root), patch.object(self.native.subprocess, 'run', side_effect=dispatch):
            result = self.native.prepare_lock(profile, catalog, output, work)
        self.assertEqual(1, len(calls))
        self.assertEqual(observed, blocks.load_json(output))
        self.assertEqual('prepared-native-lock', result['status'])
        self.assertIs(result['qualificationPerformed'], False)
        self.assertIs(result['publicAvailabilityEstablished'], False)
        self.assertFalse((work / 'qualification.json').exists())
        self.assertFalse(list(work.rglob('*.nupkg')))
        expected = self.root / 'qualification-probe'
        class LockedInputsObserved(Exception):
            pass
        def locked_dispatch(arguments, **kwargs):
            self.assertEqual(['dotnet', 'restore'], arguments[:2])
            self.assertIn('--locked-mode', arguments)
            for relative, digest in result['probeInputs'].items():
                self.assertEqual((expected / relative).read_bytes(), (work / relative).read_bytes())
                self.assertEqual(blocks.raw_sha256(expected / relative), digest)
            raise LockedInputsObserved()
        with patch.object(self.native.profile_catalogs, 'qualification_inputs', return_value={'catalog': blocks.load_json(catalog), 'nativeLock': output}), \
                patch.object(self.native.subprocess, 'run', side_effect=locked_dispatch):
            with self.assertRaises(LockedInputsObserved):
                self.native.qualify(profile, expected, catalog_path=catalog, native_lock=output,
                                    qualification_recipe=self.root / 'recipe.json')
        with patch.object(self.native.subprocess, 'run') as dispatch:
            with self.assertRaises(blocks.ResolverError):
                self.native.qualify(profile, self.root / 'must-not-qualify', catalog_path=catalog)
            dispatch.assert_not_called()

    def test_lock_preparation_preserves_existing_historical_and_failed_outputs(self):
        profile, catalog = self.preparation_inputs()
        previous = self.root / 'existing-lock.json'
        previous.write_bytes(b'historical lock bytes\n')
        with patch.object(self.native, 'ROOT', self.root), patch.object(self.native.subprocess, 'run') as dispatch:
            for output in (previous, self.root / 'tests/fixtures/default-dependency-profile/new.lock.json', self.root / 'outside/../tests/fixtures/legacy.json'):
                with self.assertRaises(ValueError):
                    self.native.prepare_lock(profile, catalog, output, self.root / 'must-not-run')
            dispatch.assert_not_called()
        self.assertEqual(b'historical lock bytes\n', previous.read_bytes())
        self.assertFalse((self.root / 'must-not-run').exists())
        output = self.root / 'new-failed.lock.json'
        failed = subprocess.CompletedProcess(['dotnet', 'restore'], 1, 'restore failed', '')
        with patch.object(self.native, 'ROOT', self.root), patch.object(self.native.subprocess, 'run', return_value=failed):
            with self.assertRaises(ValueError):
                self.native.prepare_lock(profile, catalog, output, self.root / 'failed-restore')
        self.assertFalse(output.exists())
        self.assertTrue((self.root / 'failed-restore/ordinary-restore.log').is_file())
        self.assertFalse((self.root / 'failed-restore/preparation.json').exists())

    def test_lock_preparation_missing_observed_pin_and_changed_selection_cannot_emit_output(self):
        profile, catalog = self.preparation_inputs()
        output, work = self.root / 'incomplete.lock.json', self.root / 'incomplete-restore'
        def dispatch(arguments, **kwargs):
            fixtures.write_json(work / 'Feature/packages.lock.json', {'version': 2, 'dependencies': {'net10.0': {}}})
            return subprocess.CompletedProcess(arguments, 0, 'synthetic incomplete restore', '')
        with patch.object(self.native, 'ROOT', self.root), patch.object(self.native.subprocess, 'run', side_effect=dispatch):
            with self.assertRaisesRegex(ValueError, 'omitted or changed'):
                self.native.prepare_lock(profile, catalog, output, work)
        self.assertFalse(output.exists())
        self.assertFalse((work / 'preparation.json').exists())
        selected = blocks.load_json(profile)
        selected['artifacts'].pop('nuget:Orbyss.Foundation.PostgreSql')
        fixtures.write_json(profile, selected)
        with patch.object(self.native, 'ROOT', self.root), patch.object(self.native.subprocess, 'run') as dispatch:
            with self.assertRaises(blocks.ResolverError):
                self.native.prepare_lock(profile, catalog, output, self.root / 'mismatched-selection')
            dispatch.assert_not_called()
        self.assertFalse((self.root / 'mismatched-selection').exists())

    def test_lock_preparation_cli_rejects_implicit_and_mixed_qualification_inputs(self):
        profile, catalog = self.preparation_inputs()
        common = ['--prepare-lock', str(self.root / 'new.lock.json')]
        for arguments in (common, common + ['--profile', str(profile)],
                          common + ['--profile', str(profile), '--catalog', str(catalog), '--native-lock', str(self.root / 'old.lock.json')],
                          common + ['--profile', str(profile), '--catalog', str(catalog), '--qualification-recipe', str(self.root / 'recipe.json')]):
            process = subprocess.run([sys.executable, str(ROOT / 'tests/validate_default_dependency_profile.py'), *arguments],
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual(2, process.returncode, process.stdout + process.stderr)
            self.assertIn('Lock preparation requires', process.stderr)
        self.assertFalse((self.root / 'new.lock.json').exists())


def additive(base):
    target = copy.deepcopy(base)
    contract = copy.deepcopy(base['packages']['nuget:Orbyss.Foundation.Json'])
    contract.update(packageId='Orbyss.Foundation.Authentication.Core', requires=[], activations=[], configuration=[])
    contract['materialization']['allowedRoles'] = ['core', 'implementation']
    target['packages'][CORE] = contract
    target['packages'][AUTH]['requires'].append({'package': CORE, 'targetSlot': 'dotnet'})
    target['compositions']['validated_account_contract'] = {
        'when': 'A domain consumes a validated account value contract.', 'scopeKind': 'application',
        'targetSlots': {'dotnet': {'kind': 'dotnet-project', 'allowedRoles': ['core']}},
        'requirements': [{'package': CORE, 'targetSlot': 'dotnet'}],
        'optionGroups': [], 'conflicts': [], 'configuration': []}
    target['capabilities']['validated_account_contract'] = {'suggestedCompositions': ['validated_account_contract']}
    blocks.validate_catalog(target)
    return target


class CatalogProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.registry = self.root / 'registry'
        shutil.copytree(blocks.profile_registry(), self.registry)
        self.base = blocks.load_json(blocks.default_catalog(Path(blocks.__file__)))
        self.target = additive(self.base)
        self.base_path = self.registry / 'catalogs/unit-base.json'
        self.target_path = self.registry / 'catalogs/unit-contracts.json'
        fixtures.write_json(self.base_path, self.base)
        fixtures.write_json(self.target_path, self.target)
        self.selected = blocks.dependency_profile_value(self.target, IDENTITY)
        self.profile_path = self.registry / 'unit-contracts.profile.json'
        fixtures.write_json(self.profile_path, self.selected)
        self.proof_path = self.registry / 'evidence/unit-contracts.json'
        self.receipt = {'status': 'release-validation-passed', 'source': {'clean': True},
                        'catalog': {'sha256': self.selected['catalogResolutionSha256']},
                        'steps': [{'id': 'synthetic-unit-only', 'exitCode': 0}]}
        fixtures.write_json(self.proof_path, self.receipt)
        self.index = blocks.load_json(self.registry / 'index.json')
        # Keep synthetic legacy/default-dispatch cases anchored to retained immutable evidence.
        self.index['default'] = blocks.load_json(self.registry / 'dependency-profile-default-0.12.7.json')['id']
        self.entry = {'path': self.profile_path.relative_to(self.registry).as_posix(),
                      'sha256': blocks.raw_sha256(self.profile_path), 'status': 'qualified',
                      'evidence': {'path': self.proof_path.relative_to(self.registry).as_posix(),
                                   'sha256': blocks.raw_sha256(self.proof_path)},
                      'catalogSnapshot': {'path': self.target_path.relative_to(self.registry).as_posix(),
                                          'sha256': blocks.raw_sha256(self.target_path),
                                          'base': {'path': self.base_path.relative_to(self.registry).as_posix(),
                                                   'sha256': blocks.raw_sha256(self.base_path)}}}
        self.index['profiles'][IDENTITY] = self.entry
        self.save_index()

    def save_index(self):
        fixtures.write_json(self.registry / 'index.json', self.index)

    def refresh_target(self, *, regenerate_profile=True):
        fixtures.write_json(self.target_path, self.target)
        self.entry['catalogSnapshot']['sha256'] = blocks.raw_sha256(self.target_path)
        if regenerate_profile:
            self.selected = blocks.dependency_profile_value(self.target, IDENTITY)
            fixtures.write_json(self.profile_path, self.selected)
            self.entry['sha256'] = blocks.raw_sha256(self.profile_path)
            self.receipt['catalog']['sha256'] = self.selected['catalogResolutionSha256']
            fixtures.write_json(self.proof_path, self.receipt)
            self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
        self.save_index()

    def qualified(self, supplied=None):
        return blocks.qualified_dependency_profile(self.registry, IDENTITY, supplied or self.base)

    def test_prepared_foundation_contract_catalog_is_additive_complete_and_unregistered(self):
        registry = blocks.profile_registry()
        directory = registry / 'catalogs/foundation-0-3-0-contracts'
        targets, bases = list(directory.glob('target-*.json')), list(directory.glob('base-*.json'))
        self.assertEqual(1, len(targets))
        self.assertEqual(1, len(bases))
        target, base = blocks.load_json(targets[0]), blocks.load_json(bases[0])
        self.assertEqual(blocks.raw_sha256(blocks.default_catalog(Path(blocks.__file__))), blocks.raw_sha256(bases[0]))
        blocks.validate_additive_profile_catalog(base, target)
        profile = blocks.load_json(registry / 'dependency-profile-foundation-0.3.0.json')
        self.assertEqual(target, blocks.materialize_dependency_profile(target, profile))
        index = blocks.load_json(registry / 'index.json')
        if profile['id'] in index['profiles']:
            self.assertEqual(target, blocks.qualified_dependency_profile(registry, profile['id'], base)[0])
        isolated = self.root / 'prepared-registry'
        shutil.copytree(registry, isolated)
        denied = blocks.load_json(isolated / 'index.json')
        denied['profiles'].pop(profile['id'], None)
        fixtures.write_json(isolated / 'index.json', denied)
        with self.assertRaisesRegex(blocks.ResolverError, 'unlisted'):
            blocks.qualified_dependency_profile(isolated, profile['id'], base)
        import validate_default_dependency_profile as native
        runtime = native.selected_runtime_packages(target, True)
        actual = {package['packageId'] for package in runtime.values() if package['family'] == 'foundation'}
        projects = {package['packageId'] for package in base['packages'].values()
                    if package['family'] == 'foundation' and package['materialization']['kind'] == 'nuget-project'}
        projects |= {'Orbyss.Foundation.Authentication.Core', 'Orbyss.Foundation.Collections.Core',
                     'Orbyss.Foundation.Execution', 'Orbyss.Foundation.Execution.Core',
                     'Orbyss.Foundation.PostgreSql', 'Orbyss.Foundation.Web.ProblemDetails.Core'}
        self.assertEqual(projects, actual)
        self.assertEqual(29, len(actual))
        self.assertEqual('0.3.0', profile['artifacts']['nuget:Orbyss.Foundation.Analyzers'])
        self.assertEqual('0.2.0', profile['artifacts']['nuget:Orbyss.Foundation.Build'])
        self.assertEqual('0.2.4', profile['artifacts']['nuget:Orbyss.Foundation.OpenApi.Exporter'])
        schema = ROOT / 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.schema.json'
        result = json_schema.validate_value(target, blocks.load_json(schema), schema)
        self.assertTrue(result['valid'], result)
        for composition, role, expected_activation in (
                ('validated_account_contract', 'core', False), ('ordered_value_sequence', 'core', False),
                ('problem_definition_contract', 'core', False), ('operation_deadline_contract', 'core', False),
                ('operation_deadlines', 'implementation', True), ('postgresql_units', 'provider', True)):
            consumer = self.root / ('prepared-' + composition)
            selection, architecture = fixtures.accepted_fixture(blocks, consumer, target, composition)
            value = blocks.load_json(selection)
            value['targets'][0]['role'] = role
            fixtures.write_json(selection, value)
            fixtures.refresh_registration(selection, architecture)
            resolved = blocks.resolve(consumer, selection, targets[0], 'unregistered-input-unit-only')
            self.assertEqual(expected_activation, bool(resolved['activations']))
            value['targets'][0]['role'] = 'core' if role == 'provider' else 'frontend-runtime'
            fixtures.write_json(selection, value)
            fixtures.refresh_registration(selection, architecture)
            with self.assertRaises(blocks.ResolverError):
                blocks.resolve(consumer, selection, targets[0], 'unregistered-input-unit-only')

    def add_build_family(self):
        family = copy.deepcopy(self.base['families']['foundation'])
        family.update(releaseVersion='0.2.0')
        family.pop('toolVersions', None)
        self.target['families']['foundation-build'] = family
        build = copy.deepcopy(self.base['packages']['nuget:Orbyss.Foundation.Json'])
        build.update(packageId='Orbyss.Foundation.Build', family='foundation-build', version='0.2.0',
                     requires=[], activations=[], configuration=[], supportsBuildTime=True)
        self.target['packages']['nuget:Orbyss.Foundation.Build'] = build
        self.refresh_target()

    def test_additive_independent_build_family_retains_exact_pin_and_all_legacy_families(self):
        self.add_build_family()
        self.target['families']['foundation']['releaseVersion'] = '0.3.0'
        held = self.target['families']['foundation'].get('toolVersions', {})
        for package in self.target['packages'].values():
            if package['family'] == 'foundation':
                package['version'] = held.get(package['packageId'], '0.3.0')
        self.refresh_target()
        target, selected = self.qualified()
        self.assertEqual('0.2.0', selected['artifacts']['nuget:Orbyss.Foundation.Build'])
        self.assertEqual('0.3.0', selected['artifacts']['nuget:Orbyss.Foundation.Json'])
        self.assertEqual(self.base['families'].keys() | {'foundation-build'}, target['families'].keys())
        broken = copy.deepcopy(self.target)
        broken['families'].pop('foundation')
        with self.assertRaises(blocks.ResolverError):
            blocks.validate_additive_profile_catalog(self.base, broken)

    def test_new_profile_selects_complete_snapshot_and_preserves_historical_bytes(self):
        original_registry = blocks.profile_registry()
        before = {path.relative_to(original_registry): path.read_bytes()
                  for path in original_registry.rglob('*.json')}
        for identity in blocks.load_json(original_registry / 'index.json')['profiles']:
            self.assertEqual(blocks.qualified_dependency_profile(original_registry, identity, self.base),
                             blocks.qualified_dependency_profile(self.registry, identity, self.base))
        catalog, selected = self.qualified()
        self.assertEqual(self.target, catalog)
        self.assertEqual(self.selected, selected)
        self.assertEqual(self.target, self.qualified(self.target)[0])
        self.assertEqual(set(catalog['packages']), set(selected['artifacts']))
        for relative, content in before.items():
            self.assertEqual(content, (original_registry / relative).read_bytes())
            if relative.as_posix() != 'index.json':
                self.assertEqual(content, (self.registry / relative).read_bytes())
        self.assertEqual(json.loads(before[Path('index.json')])['default'],
                         blocks.load_json(original_registry / 'index.json')['default'])

    def test_unbound_profile_and_unknown_caller_composition_are_rejected(self):
        binding = self.entry.pop('catalogSnapshot')
        self.save_index()
        with self.assertRaisesRegex(blocks.ResolverError, 'composition rules'):
            self.qualified()
        self.entry['catalogSnapshot'] = binding
        self.save_index()
        drift = copy.deepcopy(self.base)
        drift['compositions']['domain_events']['requirements'] = []
        with self.assertRaisesRegex(blocks.ResolverError, 'composition'):
            self.qualified(drift)

    def test_both_snapshot_hashes_and_safe_paths_are_required(self):
        for path in (self.base_path, self.target_path):
            with self.subTest(path=path.name):
                content = path.read_bytes()
                path.write_bytes(content + b' ')
                with self.assertRaisesRegex(blocks.ResolverError, 'catalog.*changed'):
                    self.qualified()
                path.write_bytes(content)
        for reference in (self.entry['catalogSnapshot'], self.entry['catalogSnapshot']['base']):
            original = reference['path']
            for invalid in ('../outside.json', str(self.base_path.resolve()), 'catalogs/../unit-base.json'):
                reference['path'] = invalid
                self.save_index()
                with self.assertRaises(blocks.ResolverError):
                    self.qualified()
            reference['path'] = original
        self.save_index()
        self.entry['catalogSnapshot']['unreviewedFallback'] = True
        self.save_index()
        with self.assertRaises(blocks.ResolverError):
            self.qualified()

    def test_existing_rules_identity_configuration_and_sources_cannot_drift(self):
        mutations = [
            lambda value: value['packages'][AUTH]['materialization']['allowedRoles'].append('core'),
            lambda value: value['packages'][AUTH]['activations'][0].update(featureIdentity='ChangedFeature'),
            lambda value: value['packages'][AUTH]['configuration'].append({'id': 'unreviewed'}),
            lambda value: value['sources']['nuget-org'].update(url='https://unreviewed.invalid/index.json'),
            lambda value: value['compositions']['domain_events']['requirements'].clear(),
            lambda value: value['capabilities'].pop(next(iter(self.base['capabilities']))),
            lambda value: value['families']['foundation'].update(repository='https://unreviewed.invalid/repository')]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.target = additive(self.base)
                mutate(self.target)
                self.refresh_target()
                with self.assertRaisesRegex(blocks.ResolverError, 'additive|unchanged|preserve'):
                    self.qualified()

    def test_removals_and_replaced_requirements_are_rejected_even_with_fresh_hashes(self):
        for mutate in (lambda value: value['packages'].pop('nuget:Orbyss.Foundation.Web.Discovery.Abstractions'),
                       lambda value: value['packages']['nuget:Orbyss.Foundation.DomainEvents']['requires'].clear(),
                       lambda value: value['compositions'].pop('hosted_pages')):
            self.target = additive(self.base)
            mutate(self.target)
            self.refresh_target(regenerate_profile=False)
            with self.assertRaises(blocks.ResolverError):
                self.qualified()

    def test_selected_catalog_still_requires_exact_complete_pins_and_evidence(self):
        for mutate in (lambda value: value['artifacts'].pop(CORE),
                       lambda value: value['families'].pop('foundation'),
                       lambda value: value.update(compositionSha256='0' * 64),
                       lambda value: value.update(catalogResolutionSha256='0' * 64),
                       lambda value: value['artifacts'].update({CORE: '99.0.0'})):
            changed = copy.deepcopy(self.selected)
            mutate(changed)
            fixtures.write_json(self.profile_path, changed)
            self.entry['sha256'] = blocks.raw_sha256(self.profile_path)
            self.save_index()
            with self.assertRaises(blocks.ResolverError):
                self.qualified()
        fixtures.write_json(self.profile_path, self.selected)
        self.entry['sha256'] = blocks.raw_sha256(self.profile_path)
        self.receipt['steps'][0]['exitCode'] = 1
        fixtures.write_json(self.proof_path, self.receipt)
        self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
        self.save_index()
        with self.assertRaisesRegex(blocks.ResolverError, 'receipt'):
            self.qualified()

    def test_transition_exposes_additions_and_preserves_actual_accepted_choices(self):
        consumer = self.root / 'consumer'
        consumer.mkdir()
        installed = consumer / 'installed-catalog.json'
        fixtures.write_json(installed, self.base)
        selection, architecture = fixtures.accepted_fixture(blocks, consumer, self.base)
        governance = consumer / '.specify/extensions/program-kit-governance/extension.yml'
        governance.parent.mkdir(parents=True)
        governance.write_text('extension:\n  version: "0.12.5"\n')
        original = selection.read_bytes()
        destination, packet = profiles.draft(consumer, installed, IDENTITY, self.registry)
        self.assertEqual([CORE], packet['addedArtifacts'])
        self.assertEqual([], packet['removedArtifacts'])
        self.assertIn(AUTH, packet['changedArtifacts'])
        self.assertIn(CORE, packet['changedArtifacts'])
        self.assertEqual(original, selection.read_bytes())
        decision = consumer / 'docs/architecture/decisions/additive-profile.md'
        decision.parent.mkdir(parents=True)
        decision.write_text('Accepted ' + packet['profileSha256'] + ' ' + packet['reviewSha256'])
        model = blocks.load_json(architecture)
        model['decisions'].append({'id': 'additive-profile', 'status': 'Accepted',
                                  'path': decision.relative_to(consumer).as_posix(), 'sha256': blocks.raw_sha256(decision)})
        fixtures.write_json(architecture, model)
        with patch.object(blocks, 'profile_registry', return_value=self.registry):
            profiles.accept(consumer, destination, self.registry, 'additive-profile', 'Reviewed the additive contract catalog')
        accepted = blocks.load_json(selection)
        previous = blocks.load_json(destination / 'originals/selection.json')
        for field in ('scopes', 'targets', 'instances'):
            self.assertEqual(previous[field], accepted[field])
        self.assertEqual(self.target, blocks.load_json(blocks.consumer_catalog(consumer, accepted, installed)))

    def test_snapshot_preparation_is_immutable_and_grants_no_registry_authority(self):
        output = self.root / 'prepared'
        binding = catalogs.prepare(self.base_path, self.target_path, output, 'unit-contracts')
        before = {path: path.read_bytes() for path in output.rglob('*.json')}
        self.assertEqual(binding, catalogs.prepare(self.base_path, self.target_path, output, 'unit-contracts'))
        self.assertEqual(2, len(before))
        self.assertFalse((output / 'index.json').exists())
        self.assertEqual(self.target, blocks.dependency_profile_catalog(output, {'catalogSnapshot': binding}, self.base))
        target = output / binding['path']
        target.write_bytes(before[target] + b'changed')
        with self.assertRaisesRegex(blocks.ResolverError, 'immutable catalog snapshot changed'):
            catalogs.prepare(self.base_path, self.target_path, output, 'unit-contracts')
        self.assertEqual(before[target] + b'changed', target.read_bytes())
        for path, content in before.items():
            if path != target:
                self.assertEqual(content, path.read_bytes())

    def test_additive_core_selection_materializes_with_its_physical_role(self):
        consumer = self.root / 'core-consumer'
        selection, architecture = fixtures.accepted_fixture(blocks, consumer, self.target, 'validated_account_contract')
        value = blocks.load_json(selection)
        value['targets'][0]['role'] = 'core'
        fixtures.write_json(selection, value)
        fixtures.refresh_registration(selection, architecture)
        resolved = blocks.resolve(consumer, selection, self.target_path, 'synthetic-unit-only')
        selected = {package['packageKey'] for target in resolved['targets'] for package in target.get('packages', [])}
        self.assertIn(CORE, selected)
        self.assertEqual([], resolved['activations'])
        value['targets'][0]['role'] = 'provider'
        fixtures.write_json(selection, value)
        fixtures.refresh_registration(selection, architecture)
        with self.assertRaises(blocks.ResolverError):
            blocks.resolve(consumer, selection, self.target_path, 'synthetic-unit-only')

    def test_index_schema_accepts_historical_and_bound_entries_and_rejects_unsafe_paths(self):
        path = ROOT / 'extensions/program-kit-building-blocks/references/dependency-profile-index.schema.json'
        schema = blocks.load_json(path)
        self.assertTrue(json_schema.validate_value(blocks.load_json(blocks.profile_registry() / 'index.json'), schema, path)['valid'])
        self.assertTrue(json_schema.validate_value(self.index, schema, path)['valid'])
        for mutate in (
            lambda value: value['catalogSnapshot'].update(path='../outside.json'),
            lambda value: value['catalogSnapshot'].update(path='C:/outside.json'),
            lambda value: value['catalogSnapshot'].update(path='catalogs\\\\outside.json'),
            lambda value: value['catalogSnapshot']['base'].update(path='catalogs/../outside.json'),
            lambda value: value['catalogSnapshot']['base'].update(sha256='A' * 64),
            lambda value: value['catalogSnapshot']['base'].pop('sha256'),
            lambda value: value['catalogSnapshot'].update(fallback=True)):
            invalid = copy.deepcopy(self.index)
            mutate(invalid['profiles'][IDENTITY])
            self.assertFalse(json_schema.validate_value(invalid, schema, path)['valid'])

    def named_recipe(self):
        executor = self.root / 'tests/validate_default_dependency_profile.py'
        executor.parent.mkdir(exist_ok=True)
        executor.write_bytes((ROOT / 'tests/validate_default_dependency_profile.py').read_bytes())
        native_lock = self.root / 'unit-native.lock.json'
        native_lock.write_text('{"version": 1, "dependencies": {}}\n')
        recipe_path = self.registry / 'recipes/unit.json'
        ref = lambda path, normalized=False: {'path': path.relative_to(self.root).as_posix(),
                                             'sha256': catalogs.source_sha256(path) if normalized else blocks.raw_sha256(path)}
        value = {'schemaVersion': 1, 'id': 'synthetic-contracts-qualification',
                 'profile': {**ref(self.profile_path), 'id': IDENTITY}, 'families': self.selected['families'],
                 'catalogSnapshot': {**ref(self.target_path), 'base': ref(self.base_path)},
                 'nativeLock': ref(native_lock, True), 'executor': ref(executor, True)}
        fixtures.write_json(recipe_path, value)
        return recipe_path, value, executor, native_lock

    def test_named_recipe_binds_all_paths_versions_executor_and_lock_before_operations(self):
        recipe_path, recipe, executor, native_lock = self.named_recipe()
        inputs = lambda: catalogs.qualification_inputs(self.profile_path, self.target_path, native_lock,
                                                       recipe_path, executor, self.root)
        selected = inputs()
        self.assertEqual(self.target, selected['catalog'])
        self.assertEqual(native_lock.resolve(), selected['nativeLock'])
        self.assertEqual(blocks.raw_sha256(recipe_path), selected['qualificationRecipeSha256'])
        schema_path = ROOT / 'extensions/program-kit-building-blocks/references/dependency-qualification-recipe.schema.json'
        schema = blocks.load_json(schema_path)
        self.assertTrue(json_schema.validate_value(recipe, schema, schema_path)['valid'])
        for mutate in (lambda value: value['profile'].update(id='unbound-profile'),
                       lambda value: value['profile'].update(sha256='0' * 64),
                       lambda value: value['families']['foundation'].update(releaseVersion='99.0.0'),
                       lambda value: value['catalogSnapshot']['base'].update(sha256='0' * 64),
                       lambda value: value['executor'].update(sha256='0' * 64),
                       lambda value: value['nativeLock'].update(path='../unsafe.lock.json'),
                       lambda value: value.update(defaultPromotionPerformed=True)):
            changed = copy.deepcopy(recipe)
            mutate(changed)
            fixtures.write_json(recipe_path, changed)
            with self.assertRaises(blocks.ResolverError):
                inputs()
        fixtures.write_json(recipe_path, recipe)
        for path in (self.profile_path, self.target_path, self.base_path, executor, native_lock):
            original = path.read_bytes()
            path.write_bytes(original + b' changed')
            with self.assertRaises(blocks.ResolverError):
                inputs()
            path.write_bytes(original)
        alias = self.root / 'same-lock-different-path.json'
        alias.write_bytes(native_lock.read_bytes())
        with self.assertRaisesRegex(blocks.ResolverError, 'path or hash'):
            catalogs.qualification_inputs(self.profile_path, self.target_path, alias, recipe_path, executor, self.root)
        with self.assertRaisesRegex(blocks.ResolverError, 'paired'):
            catalogs.qualification_inputs(self.profile_path, self.target_path, None, recipe_path, executor, self.root)

    def test_partial_candidate_cli_inputs_fail_before_package_or_host_operations(self):
        scripts = [
            ('tests/validate_default_dependency_profile.py', ['--profile', str(self.profile_path), '--catalog', str(self.target_path)]),
            ('tests/validate_published_forms_browser.py', ['--catalog', str(self.target_path)]),
            ('tests/validate_bootstrap_runtime.py', ['--catalog', str(self.target_path)])]
        for script, arguments in scripts:
            process = subprocess.run([sys.executable, str(ROOT / script), *arguments], cwd=self.root,
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual(2, process.returncode, process.stdout + process.stderr)
            self.assertIn('requires', process.stderr.lower())
        sys.path.insert(0, str(ROOT / 'scripts'))
        import validate_default_dependency_profile as native
        output = self.root / 'must-not-run'
        with patch.object(native.subprocess, 'run') as dispatch:
            with self.assertRaises(blocks.ResolverError):
                native.qualify(self.profile_path, output, catalog_path=self.target_path)
            dispatch.assert_not_called()
        self.assertFalse(output.exists())
        from build_dependency_qualification import build
        with self.assertRaisesRegex(blocks.ResolverError, 'paired'):
            build(self.profile_path, self.root / 'missing-native', self.root / 'missing-browser',
                  self.root / 'missing-availability.json', self.root / 'missing-host', catalog_path=self.target_path)
        process = subprocess.run([sys.executable, str(ROOT / 'tests/validate_published_forms_browser.py'),
                                  '--profile', str(self.profile_path), '--catalog', str(self.target_path),
                                  '--prepare-only', '--engines=chromium,webkit'], cwd=self.root,
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(0, process.returncode, process.stdout + process.stderr)
        prepared = json.loads(process.stdout)
        self.assertTrue(prepared['prepared'])
        self.assertEqual(0, prepared['paidSessionsStarted'])
        self.assertEqual(0, prepared['packageOperationsStarted'])
        self.assertEqual(self.selected['artifacts']['npm:@orbyss-io/forms-contracts'],
                         prepared['packages']['dependencies']['@orbyss-io/forms-contracts'])

    def test_registered_named_recipe_matches_profile_catalog_and_generic_evidence(self):
        self.add_build_family()
        for name in ('Orbyss.Foundation.Collections.Core', 'Orbyss.Foundation.PostgreSql'):
            package = copy.deepcopy(self.base['packages']['nuget:Orbyss.Foundation.Json'])
            package.update(packageId=name, requires=[], activations=[], configuration=[])
            self.target['packages']['nuget:' + name] = package
        self.refresh_target()
        recipe_path, recipe, executor, native_lock = self.named_recipe()
        original_index = blocks.load_json(blocks.profile_registry() / 'index.json')
        legacy = blocks.load_json(blocks.profile_registry() / 'dependency-profile-default-0.12.7.json')['id']
        original = original_index['profiles'][legacy]
        receipt = blocks.load_json(blocks.profile_registry() / original['evidence']['path'])
        receipt['catalog']['sha256'] = self.selected['catalogResolutionSha256']
        receipt['source'].update(recipeSha256=catalogs.source_sha256(executor), lockSha256=catalogs.source_sha256(native_lock),
                                 qualificationRecipeSha256=blocks.raw_sha256(recipe_path))
        official_tools = {}
        for identity in ('Orbyss.Foundation.Build', 'Orbyss.Foundation.OpenApi.Exporter'):
            version = self.selected['artifacts']['nuget:' + identity]
            official_tools[identity] = {'id': identity, 'version': version, 'sha256': '1' * 64,
                                       'source': 'https://api.nuget.org/v3/index.json', 'nativeSource': None,
                                       'archiveUrl': 'https://api.nuget.org/v3-flatcontainer/' + identity.lower() + '/' + version + '/' + identity.lower() + '.' + version + '.nupkg',
                                       'nativeProvenanceSha256': '2' * 64}
        tool_proof = self.root / 'official-tools.json'
        import validate_default_dependency_profile as native
        native.write(tool_proof, official_tools)
        receipt['source'].update(officialTools=official_tools, officialToolsSha256=blocks.raw_sha256(tool_proof))
        for identity, artifact in receipt['artifacts'].items():
            if 'nuget:' + identity in self.selected['artifacts']:
                artifact['version'] = self.selected['artifacts']['nuget:' + identity]
        for package in self.target['packages'].values():
            if package['ecosystem'] == 'nuget' and package['materialization']['kind'] == 'nuget-project':
                receipt['artifacts'].setdefault(package['packageId'], {'version': package['version'], 'sha256': '3' * 64})
        for identity, binding in official_tools.items():
            receipt['artifacts'][identity] = {'version': binding['version'], 'sha256': binding['sha256']}
        available = {item['packageKey']: item for item in receipt['availableArtifacts']}
        receipt['availableArtifacts'] = [{**available.get(key, {'packageKey': key}), 'version': version}
                                        for key, version in self.selected['artifacts'].items()]
        browser = receipt['browserIntegration']
        browser['profile']['catalogResolutionSha256'] = self.selected['catalogResolutionSha256']
        browser['profile']['packages'] = {key: self.selected['artifacts']['npm:' + key]
                                         for key in browser['profile']['packages']}
        host = receipt['hostRuntime']
        host['inputs'].update(catalogResolutionSha256=self.selected['catalogResolutionSha256'],
                              foundationRelease=self.selected['families']['foundation']['releaseVersion'])
        for step in receipt['steps']:
            if step['id'] == 'published-forms-browser': step['evidenceSha256'] = blocks.canonical_sha256(browser)
            if step['id'] == 'published-host-runtime': step['evidenceSha256'] = blocks.canonical_sha256(host)
        fixtures.write_json(self.proof_path, receipt)
        self.entry.update(evidence={'path': self.proof_path.relative_to(self.registry).as_posix(), 'sha256': blocks.raw_sha256(self.proof_path)},
                          recipeSha256=receipt['source']['recipeSha256'], nativeLockSha256=receipt['source']['lockSha256'],
                          allowedActivations=receipt['scope']['allowedActivations'],
                          qualificationRecipe={'path': recipe_path.relative_to(self.registry).as_posix(), 'sha256': blocks.raw_sha256(recipe_path)})
        self.save_index()
        self.assertEqual(self.target, self.qualified()[0])
        for identity in ('Orbyss.Foundation.Collections.Core', 'Orbyss.Foundation.PostgreSql'):
            original = copy.deepcopy(receipt['artifacts'][identity])
            for changed in (None, {**original, 'version': '99.0.0'}, {**original, 'sha256': 'tampered'}):
                if changed is None:
                    receipt['artifacts'].pop(identity)
                else:
                    receipt['artifacts'][identity] = changed
                fixtures.write_json(self.proof_path, receipt)
                self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
                self.save_index()
                with self.assertRaisesRegex(blocks.ResolverError, 'artifact'):
                    self.qualified()
            receipt['artifacts'][identity] = original
        for identity in official_tools:
            original = copy.deepcopy(receipt['artifacts'][identity])
            receipt['artifacts'][identity]['sha256'] = '7' * 64
            fixtures.write_json(self.proof_path, receipt)
            self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
            self.save_index()
            with self.assertRaisesRegex(blocks.ResolverError, 'source proof'):
                self.qualified()
            receipt['artifacts'][identity] = original
        fixtures.write_json(self.proof_path, receipt)
        self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
        self.save_index()
        import validate_default_dependency_profile as native
        original_default = self.index['default']
        legacy_path = blocks.repository_path(self.registry, self.index['profiles'][original_default]['path'])
        with patch.object(blocks, 'profile_registry', return_value=self.registry):
            self.assertEqual((legacy_path, None, None, None), native.default_qualification_inputs())
        self.index['default'] = IDENTITY  # Isolated synthetic unit registry, never the shipped index.
        self.save_index()
        with patch.object(blocks, 'profile_registry', return_value=self.registry), \
                patch.object(native, 'ROOT', self.root), patch.object(native, '__file__', str(executor)):
            self.assertEqual((self.profile_path, self.target_path, native_lock, recipe_path), native.default_qualification_inputs())
            self.entry['status'] = 'unqualified'
            self.save_index()
            with self.assertRaisesRegex(blocks.ResolverError, 'unqualified'):
                native.default_qualification_inputs()
            self.entry['status'] = 'qualified'
            self.save_index()
            complete = copy.deepcopy(receipt)
            receipt['steps'].pop()
            fixtures.write_json(self.proof_path, receipt)
            self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
            self.save_index()
            with self.assertRaises(blocks.ResolverError):
                native.default_qualification_inputs()
            receipt = complete
            fixtures.write_json(self.proof_path, receipt)
            self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
            self.save_index()
        for mutate in (lambda value: value['profile'].update(id='another-profile'),
                       lambda value: value.update(defaultPromotionPerformed=True),
                       lambda value: value.update(schemaVersion=99),
                       lambda value: value['profile'].update(sha256='0' * 64),
                       lambda value: value['executor'].update(sha256='0' * 64),
                       lambda value: value['nativeLock'].update(sha256='0' * 64),
                       lambda value: value['catalogSnapshot']['base'].update(sha256='0' * 64)):
            changed = copy.deepcopy(recipe)
            mutate(changed)
            fixtures.write_json(recipe_path, changed)
            self.entry['qualificationRecipe']['sha256'] = blocks.raw_sha256(recipe_path)
            receipt['source']['qualificationRecipeSha256'] = blocks.raw_sha256(recipe_path)
            fixtures.write_json(self.proof_path, receipt)
            self.entry['evidence']['sha256'] = blocks.raw_sha256(self.proof_path)
            self.save_index()
            with self.assertRaisesRegex(blocks.ResolverError, 'named qualification recipe differs'):
                self.qualified()


if __name__ == '__main__':
    unittest.main()
