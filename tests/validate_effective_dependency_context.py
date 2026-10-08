"""Consumer dependency authority and actual maintained preparation regressions."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'extensions/program-kit-governance/scripts')]
import validate_bootstrap_provider_context as provider_tests
from validate_building_blocks import load_module, write_json, RESOLVER, CATALOG, accepted_fixture, refresh_registration
import bootstrap_provider_context as providers
import bootstrap_context
import dependency_audit
import bootstrap_compatibility

HOST = 'oci:ghcr.io/orbyss-io/foundation-host'

class EffectiveContextTests(unittest.TestCase):
    setUp = provider_tests.ProviderContextTests.setUp

    def selected(self, identity=None):
        self.blocks = load_module(self.root / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        catalog = self.blocks.new_project_catalog(identity)
        selection = json.loads(self.selection.read_text())
        selection['catalog'] = self.blocks.catalog_binding(catalog)
        write_json(self.selection, selection)
        path = self.root / 'catalog.json'
        write_json(path, catalog)
        self.blocks.preserve_dependency_profile(self.root, selection, path)
        return catalog

    def test_fresh_scaffold_and_retained_authority(self):
        self.selection.unlink()
        blocks = load_module(self.root / '.specify/extensions/program-kit-building-blocks/scripts/building_blocks.py')
        fresh = blocks.effective_dependency_context(self.root)
        self.assertEqual('0.3.1', fresh['catalog']['packages'][HOST]['version'])
        self.assertEqual('qualified-default', fresh['authority'])
        identity = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        catalog = blocks.new_project_catalog(identity)
        entry = blocks.load_json(blocks.profile_registry() / 'index.json')['profiles'][identity]
        record = {'profile': identity, 'catalogResolutionSha256': blocks.catalog_resolution_sha256(catalog), 'entrySha256': blocks.canonical_sha256(entry)}
        write_json(self.root / '.program-kit/managed.json', {'newProjectDependencyProfile': record})
        value = providers.project(self.root, self.decisions, require_selection=False)
        self.assertEqual('0.2.4', value['managed_baseline_evidence']['releaseVersion'])
        engineering = load_module(ROOT / 'extensions/program-kit-dotnet/scripts/dependency_profile.py')
        self.assertEqual(record, engineering.engineering_default(self.root))
        self.assertEqual(catalog, engineering.retained_catalog(self.root))
        reference = self.root / '.specify/extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md'
        reference.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md', reference)
        runtime = bootstrap_context.runtime_release_projection(self.root, {'routing': {'capabilities': ['dotnet-host-runtime']}})
        pin_authority = json.loads((self.root / runtime['managed_host']['catalog']).read_text())
        self.assertEqual(runtime['managed_host']['version'], pin_authority['artifacts'][HOST])
        self.assertEqual('qualified-exact-profile', runtime['managed_host']['catalogKind'])
        record['entrySha256'] = 'f' * 64
        write_json(self.root / '.program-kit/managed.json', {'newProjectDependencyProfile': record})
        with self.assertRaisesRegex(ValueError, 'scaffold authority changed'):
            blocks.effective_dependency_context(self.root)

    def test_draft_accepted_continuity_and_legacy_after_upgrade(self):
        catalog = self.selected()
        draft = self.blocks.effective_dependency_context(self.root)
        selected = json.loads(self.selection.read_text()); selected['status'] = 'Accepted'
        write_json(self.selection, selected)
        accepted = self.blocks.effective_dependency_context(self.root)
        for key in ('catalog', 'profile', 'sharedAbi', 'resolutionSha256'):
            self.assertEqual(draft[key], accepted[key])
        self.assertEqual('0.2.5', catalog['packages']['nuget:Orbyss.Foundation.OpenApi.Exporter']['version'])
        self.assertEqual('0.2.1', catalog['families']['forms']['releaseVersion'])
        # An upgraded installation with an uncaptured historical selection keeps its exact base.
        (self.root / '.program-kit/dependency-profile.json').unlink()
        selected['catalog'] = self.blocks.catalog_binding(self.blocks.load_json(CATALOG))
        write_json(self.selection, selected)
        self.assertEqual('0.2.2', self.blocks.effective_dependency_context(self.root)['catalog']['packages'][HOST]['version'])

    def test_projections_and_both_ownership_audits_use_new_catalog(self):
        catalog = self.selected()
        dotnet = self.root / '.specify/extensions/program-kit-dotnet'
        shutil.copytree(ROOT / 'extensions/program-kit-dotnet', dotnet, dirs_exist_ok=True)
        intake = {'routing': {'capabilities': ['dotnet-host-runtime']}}
        projected = bootstrap_context.runtime_release_projection(self.root, intake)
        self.assertEqual('0.3.1', projected['managed_host']['version'])
        self.selection, architecture = accepted_fixture(self.blocks, self.root, catalog, 'api_baseline')
        selection = json.loads(self.selection.read_text())
        selection['targets'].append({'id': 'repository', 'kind': 'repository', 'path': 'Directory.Build.props', 'role': 'repository', 'scope': 'application'})
        selection['instances'][0]['targetBindings']['repository'] = 'repository'
        write_json(self.selection, selection); refresh_registration(self.selection, architecture)
        base = self.blocks.load_json(CATALOG)
        for capability in set(catalog['capabilities']) - set(base['capabilities']):
            self.assertIsNotNone(bootstrap_context.building_block_stage_contract(self.root, {'routing': {'capabilities': [capability]}}))
        for key in set(catalog['packages']) - set(base['packages']):
            if not key.startswith('nuget:'): continue
            identity = catalog['packages'][key]['packageId']
            with patch('repository_sync.provider', return_value=self.blocks):
                errors = dependency_audit.planned_selection_errors(self.root, [{'path': 'src/Unbound/Unbound.csproj', 'packageReferences': [identity]}])
            self.assertTrue(any('PKA016' in error for error in errors), identity)
            path = self.root / 'src/Unbound/Unbound.csproj'; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<Project><ItemGroup><PackageReference Include="' + identity + '" Version="0.3.1" /></ItemGroup></Project>')
            with self.assertRaisesRegex(ValueError, 'PKB405'):
                self.blocks.check_materialization(self.root, {'managedOutputs': []})

    def test_stale_summary_has_scoped_repair_and_context_sources_bind_retained_profile(self):
        self.selected()
        effective = self.blocks.effective_dependency_context(self.root)
        summary = bootstrap_context.dependency_summary(self.root, effective)
        self.assertEqual('0.3.1', summary['hostVersion'])
        radar = self.root / 'docs/architecture/technology-radar.md'
        radar.write_text('Foundation family 0.3.1 and the supplied host catalog 0.2.2/v0.2.2 have independent identities.')
        before = self.selection.read_bytes()
        with self.assertRaisesRegex(bootstrap_context.ContextError, 'scoped tooling review'):
            bootstrap_context.dependency_summary(self.root, effective)
        self.assertEqual(before, self.selection.read_bytes())
        payload = {'dependency_context': {'sources': [
            {'path': Path(path).relative_to(self.root).as_posix(), 'sha256': sha}
            for path, sha in effective['sources'].items()]},
            'reading_policy': {'allowed_sources': []}, 'evidence_index': {}}
        evidence = {'artifacts': []}
        paths = bootstrap_context.bind_projected_sources(self.root, payload, evidence)
        self.assertIn('.program-kit/dependency-profile.json', paths)
        self.assertTrue(any(path.endswith('engineering-contracts.json') for path in paths))

    def test_corrupt_or_mixed_authority_never_falls_back(self):
        self.selected()
        record_path = self.root / '.program-kit/dependency-profile.json'
        record = json.loads(record_path.read_text())
        record['resolutionSha256'] = 'f' * 64; write_json(record_path, record)
        with self.assertRaisesRegex(ValueError, 'PKB111'):
            providers.project(self.root, self.decisions)

    def test_qualification_and_shared_abi_conflicts_are_not_other_profiles(self):
        self.selected()
        record_path = self.root / '.program-kit/dependency-profile.json'
        record = json.loads(record_path.read_text())
        identity = 'foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2'
        entry = self.blocks.load_json(self.blocks.profile_registry() / 'index.json')['profiles'][identity]
        record['newProjectQualification'] = {'profile': identity, 'entrySha256': self.blocks.canonical_sha256(entry)}
        write_json(record_path, record)
        with self.assertRaisesRegex(ValueError, 'PKB610|profile differs'):
            self.blocks.effective_dependency_context(self.root)
        record.pop('newProjectQualification'); write_json(record_path, record)
        abi_path = self.blocks.profile_registry() / 'engineering-contracts.json'
        abi = self.blocks.load_json(abi_path); abi['releases']['0.3.1']['sourceCommit'] = 'a' * 40
        write_json(abi_path, abi)
        with self.assertRaisesRegex(ValueError, 'different source commits'):
            self.blocks.effective_dependency_context(self.root)

    def test_retained_recipe_protocols_and_abi_are_version_aware(self):
        for extension in ('program-kit-governance', 'program-kit-dotnet'):
            shutil.copytree(ROOT / 'extensions' / extension, self.root / '.specify/extensions' / extension, dirs_exist_ok=True)
        decisions = copy.deepcopy(self.decisions)
        decisions['web'] = {'secure_profile': 'bff-cookie-v1'}
        decisions['toolchain'] = {'pins': {'dotnet-sdk': '10.0.401'}}
        write_json(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
        renderer = load_module(self.root / '.specify/extensions/program-kit-governance/scripts/managed_provider_probes.py')
        profiles = ['foundation-0.2.4-exporter-0.2.4-forms-0.2.1-localization-0.1.2',
                    'foundation-0.3.0-build-0.3.0-exporter-0.2.4-forms-0.2.1-localization-0.1.2']
        for identity in profiles:
            catalog = self.selected(identity)
            for kind in ('foundation-activation', 'bff-keycloak'):
                name = kind + '-' + catalog['families']['foundation']['releaseVersion'].replace('.', '-')
                recipe = renderer.render(self.root, kind, name, 'ghcr.io/orbyss-io/foundation-host@sha256:' + 'a'*64)
                contract = json.loads((self.root / recipe['recipe']).with_suffix('.contract.json').read_text())
                pins = json.loads((self.root / contract['fixtures']['runtime-inputs.json']).read_text())
                runtime = load_module(self.root / '.specify/extensions/program-kit-governance/examples/bootstrap-runtime/runtime_probe.py')
                self.assertEqual(catalog['families']['foundation']['releaseVersion'] == '0.3.0', runtime.contracts_profile(pins))
                for target in contract['dependencyTargets']:
                    if not target.endswith('.csproj'): continue
                    refs = ET.parse(self.root / contract['fixtures'][target])
                    for ref in refs.iter('PackageReference'):
                        package = catalog['packages'].get('nuget:' + ref.get('Include'))
                        if package: self.assertEqual(package['version'], ref.get('Version'))

    def test_both_recipes_prepare_exact_pins_and_protocol(self):
        catalog = self.selected()
        for extension in ('program-kit-governance', 'program-kit-dotnet'):
            shutil.copytree(ROOT / 'extensions' / extension, self.root / '.specify/extensions' / extension, dirs_exist_ok=True)
        decisions = copy.deepcopy(self.decisions)
        decisions['web'] = {'secure_profile': 'bff-cookie-v1'}
        decisions['toolchain'] = {'pins': {'dotnet-sdk': '10.0.100'}}
        write_json(self.root / 'docs/architecture/bootstrap-decisions.json', decisions)
        renderer = load_module(self.root / '.specify/extensions/program-kit-governance/scripts/managed_provider_probes.py')
        for kind in ('foundation-activation', 'bff-keycloak'):
            recipe = renderer.render(self.root, kind, kind, 'ghcr.io/orbyss-io/foundation-host@sha256:' + 'a'*64)
            contract = json.loads((self.root / recipe['recipe']).with_suffix('.contract.json').read_text())
            scratch = self.root / ('scratch-' + kind); scratch.mkdir()
            with patch.object(bootstrap_compatibility, 'configuration', return_value=({'dotnet': '10.0.100'}, {})):
                inputs, plan = bootstrap_compatibility.prepare(self.root, scratch, contract)
            self.assertTrue(plan)
            pins = json.loads((scratch / 'runtime-inputs.json').read_text())
            self.assertEqual('0.3.1', pins['foundationRelease'])
            for project in scratch.rglob('*.csproj'):
                for ref in ET.parse(project).iter('PackageReference'):
                    identity = ref.get('Include')
                    expected = catalog['packages'].get('nuget:' + identity, {}).get('version', pins['sharedAbi']['pins'].get(identity))
                    if expected: self.assertEqual(expected, ref.get('Version'))
                self.assertEqual('false', next(ET.parse(project).iter('RestoreEnablePackagePruning')).text)
            runtime = load_module(scratch / 'runtime_probe.py')
            self.assertTrue(runtime.contracts_profile(pins))
            self.assertIn('provision_public_host', (self.root / recipe['recipe']).read_text())
            config = self.root / contract['fixtures']['runtime-inputs.json']; pins['foundationRelease'] = '0.2.2'
            # Mixed recipe facts must fail before provisioning, even with valid source hashes.
            pins['sharedAbi']['pins']['CShells.Abstractions'] = 'wrong'
            write_json(config, pins)
            with patch.object(bootstrap_compatibility, 'configuration', return_value=({}, {})):
                with self.assertRaisesRegex(ValueError, 'recipe authority is stale'):
                    bootstrap_compatibility.prepare(self.root, scratch, contract)

if __name__ == '__main__': unittest.main()
