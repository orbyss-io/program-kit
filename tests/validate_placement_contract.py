"""Producer-visible placement contracts reject the real bootstrap's failed path forms."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from owned_fixture import FixtureDirectory
import unittest

import validate_building_blocks as blocks_test
import validate_bootstrap_context as context_test
import validate_json_schema as schema_test

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ROOT / 'extensions/program-kit-building-blocks'


class PlacementContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = FixtureDirectory(prefix='placement-contract-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        installed = self.root / '.specify/extensions/program-kit-building-blocks/references'
        installed.mkdir(parents=True)
        for name in ('building-block-selection.schema.json', 'orbyss-building-blocks.json'):
            shutil.copyfile(BLOCKS / 'references' / name, installed / name)
        shutil.copytree(BLOCKS / 'references/dependency-profiles', installed / 'dependency-profiles')
        self.blocks = blocks_test.load_module(blocks_test.RESOLVER)
        self.context = context_test.load_module(ROOT)
        self.schema = self.blocks.load_json(installed / 'building-block-selection.schema.json')
        self.intake = {'routing': {'capabilities': ['dotnet-host-runtime', 'forms', 'openapi-contracts']}}
        adr = self.root / 'docs/decision.md'
        context_test.write(adr, '# Synthetic Proposed placement\n')
        self.selection = {'scopes': [{'id': 'app', 'kind': 'application', 'environment': 'test'}],
                          'authority': {'architectureMap': 'docs/map.json', 'decisionIds': ['placement']}, 'targets': []}
        context_test.write_json(self.root / 'docs/map.json', {
            'elements': [{'id': 'reservations', 'ownership': 'Reservations', 'decision_refs': ['placement']}],
            'decisions': [{'id': 'placement', 'path': 'docs/decision.md', 'status': 'Proposed', 'sha256': self.blocks.raw_sha256(adr)}]})

    def target(self, kind, path, **fields):
        return dict(id=kind, kind=kind, path=path, role='implementation', scope='app',
                    placement={'state': 'planned', 'owner': 'reservations', 'decisionIds': ['placement'], 'rationale': 'Synthetic test'}, **fields)

    def validate(self, target):
        self.blocks.validate_placements(self.root, {**self.selection, 'targets': [target]})

    def schema_accepts(self, target):
        schema = {'$schema': self.schema['$schema'], '$defs': self.schema['$defs'],
                  **self.schema['properties']['targets']['items']}
        return schema_test.tool.validate_value(target, schema)['valid']

    def test_all_required_kinds_reach_producer_from_same_executable_schema(self):
        contract = self.context.building_block_stage_contract(self.root, self.intake)
        planning = contract['placement_planning']
        rules = planning['target_kind_contracts']
        self.assertEqual(set(rules), {'repository', 'dotnet-project', 'npm-package', 'cshell-shell', 'dotnet-tool-manifest', 'host-image'})
        self.assertEqual(rules, self.blocks.placement_kind_contracts())
        self.assertEqual(planning['contract_source']['sha256'], self.blocks.raw_sha256(self.root / planning['contract_source']['path']))
        for kind, rule in rules.items():
            for path in rule['properties']['path']['examples']:
                target = self.target(kind, path)
                for field in set(rule['required']) - {'kind', 'path'}:
                    target[field] = rule['properties'][field]['examples'][0]
                with self.subTest(kind=kind, path=path):
                    self.validate(target)
                    self.assertTrue(self.schema_accepts(target))
                    self.assertFalse((self.root / path).exists(), 'Projection or validation must not scaffold')
        self.assertIn('runtime shell identity', rules['cshell-shell']['description'])
        self.assertIn('host DLL', rules['host-image']['description'])

    def test_actual_failed_shell_and_host_forms_fail_before_any_paid_dispatch(self):
        for kind, path in [('cshell-shell', 'shells/lending-local.json'),
                           ('cshell-shell', 'src/ReservationManagement/Composition/LendingShell.cs'),
                           ('host-image', 'runtime/lending-local/Orbyss.Foundation.Host.dll'), ('host-image', 'Dockerfile')]:
            target = self.target(kind, path, shell='lending-local')
            with self.subTest(path=path):
                with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB303.*(shells.json|hostsettings.json)'):
                    self.validate(target)
                self.assertFalse(self.schema_accepts(target))
        shell = self.target('cshell-shell', 'composition/shells.json')
        with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB102.*Runtime shell identity'):
            self.validate(shell)
        self.assertFalse(self.schema_accepts(shell))
        shell['shell'] = 'lending-local'
        self.validate(shell)
        self.assertTrue(self.schema_accepts(shell))
        self.validate(self.target('host-image', 'runtime/lending-local/hostsettings.json'))

    def test_other_kind_shapes_and_case_preserve_previous_enforcement(self):
        cases = [('repository', 'config/Directory.Build.props', 'Directory.Packages.props'),
                 ('dotnet-project', 'src/Reservations/Reservations.CSPROJ', 'src/Reservations.cs'),
                 ('npm-package', 'web/Package.JSON', 'web/package-lock.json'),
                 ('dotnet-tool-manifest', '.config/DOTNET-TOOLS.JSON', '.config/tool.exe'),
                 ('host-image', 'runtime/hostsettings.json', 'runtime/image.yaml')]
        for kind, valid, invalid in cases:
            with self.subTest(kind=kind):
                self.validate(self.target(kind, valid))
                self.assertTrue(self.schema_accepts(self.target(kind, valid)))
                with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB303'):
                    self.validate(self.target(kind, invalid))
                self.assertFalse(self.schema_accepts(self.target(kind, invalid)))

    def test_missing_kind_contract_is_a_pre_dispatch_error(self):
        path = self.root / '.specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json'
        value = copy.deepcopy(self.schema)
        value['$defs']['targetKindPlacement']['oneOf'] = [rule for rule in value['$defs']['targetKindPlacement']['oneOf'] if rule['properties']['kind']['const'] != 'cshell-shell']
        context_test.write_json(path, value)
        with self.assertRaisesRegex(self.context.ContextError, 'before dispatch'):
            self.context.building_block_stage_contract(self.root, self.intake)

    def test_legacy_selection_without_placement_remains_readable(self):
        target = self.target('cshell-shell', 'historic-custom.json')
        del target['placement']
        self.validate(target)
        self.assertTrue(self.schema_accepts(target))

    def provenance_selection(self, target, status='Accepted'):
        return {**copy.deepcopy(self.selection), 'status': status, 'targets': [target],
                'instances': [{'id': 'synthetic-placement', 'composition': 'domain_events'}]}

    def test_accepted_planned_origins_survive_materialization_without_rewriting(self):
        for kind, path, fields in (
            ('repository', 'Directory.Build.props', {}),
            ('dotnet-project', 'src/Reservations/Reservations.csproj', {}),
            ('npm-package', 'web/package.json', {}),
            ('cshell-shell', 'shells.json', {'shell': 'reservations'}),
            ('dotnet-tool-manifest', '.config/dotnet-tools.json', {}),
            ('host-image', 'runtime/hostsettings.json', {}),
        ):
            with self.subTest(kind=kind):
                selection = self.provenance_selection(self.target(kind, path, **fields))
                original = copy.deepcopy(selection)
                self.blocks.validate_placements(self.root, selection, require_all=True)
                target = self.root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'Synthetic scaffold-owned bytes\n')
                for required in (False, True):
                    self.blocks.validate_placements(self.root, selection, require_all=required)
                self.assertEqual(original, selection)
                self.assertEqual(b'Synthetic scaffold-owned bytes\n', target.read_bytes())
                draft = {**selection, 'status': 'Draft'}
                with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB306.*already observed'):
                    self.blocks.validate_placements(self.root, draft, require_all=True)
                draft['targets'][0]['placement']['state'] = 'observed'
                self.blocks.validate_placements(self.root, draft, require_all=True)

    def test_accepted_origins_keep_provenance_identity_and_file_kind_checks(self):
        target = self.target('dotnet-project', 'src/Reservations/Reservations.csproj')
        project = self.root / target['path']; project.parent.mkdir(parents=True)
        project.write_text('<Project />')
        base = self.provenance_selection(target)
        cases = (
            ('unknown owner', 'PKB306', lambda t: t['placement'].update(owner='unknown')),
            ('inactive decision', 'PKB306', lambda t: t['placement'].update(decisionIds=['unknown'])),
            ('case changed', 'PKB301', lambda t: t.update(path='src/reservations/Reservations.csproj')),
            ('file absent', 'PKB306', lambda t: (t.update(path='src/Missing.csproj'), t['placement'].update(state='observed'))),
            ('wrong file kind', 'PKB300', lambda t: t.update(path='src/Reservations')),
            ('wrong target kind', 'PKB303', lambda t: t.update(kind='npm-package')),
            ('outside repository', 'PKB300', lambda t: t.update(path='../Escaped.csproj')),
            ('internal target', 'PKB300', lambda t: t.update(path='.specify/Hidden.csproj')),
        )
        for name, code, change in cases:
            with self.subTest(case=name):
                selection = copy.deepcopy(base); change(selection['targets'][0])
                with self.assertRaisesRegex(self.blocks.ResolverError, code):
                    self.blocks.validate_placements(self.root, selection, require_all=True)
        adr = self.root / 'docs/decision.md'; original = adr.read_bytes()
        adr.write_bytes(original + b'Changed semantic decision\n')
        with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB306.*stale decision'):
            self.blocks.validate_placements(self.root, base, require_all=True)
        adr.write_bytes(original)
        for field in ('placement', 'instances'):
            with self.subTest(missing=field):
                selection = copy.deepcopy(base)
                if field == 'placement': selection['targets'][0].pop(field)
                else: selection[field] = []
                with self.assertRaisesRegex(self.blocks.ResolverError, 'PKB306'):
                    self.blocks.validate_placements(self.root, selection, require_all=True)

    def test_accepted_cli_preserves_planned_origin_after_repository_and_project_scaffold(self):
        catalog = self.blocks.load_json(blocks_test.CATALOG)
        selection_path, map_path = blocks_test.accepted_fixture(self.blocks, self.root, catalog)
        selection = self.blocks.load_json(selection_path)
        selection['targets'].append({'id': 'repository', 'kind': 'repository', 'path': 'Directory.Build.props',
                                     'role': 'build', 'scope': 'application'})
        for target in selection['targets']:
            target['placement'] = {'state': 'planned', 'owner': 'reservations',
                                   'decisionIds': ['use-building-blocks'], 'rationale': 'Accepted synthetic placement'}
        architecture = self.blocks.load_json(map_path)
        architecture['elements'] = [{'id': 'reservations', 'ownership': 'Reservations', 'decision_refs': ['use-building-blocks']}]
        adr = self.root / 'docs/decision.md'; adr.write_text('# Synthetic placement\nStatus: Accepted\n')
        architecture['decisions'] = [{'id': 'use-building-blocks', 'status': 'Accepted',
                                     'path': 'docs/decision.md', 'sha256': self.blocks.raw_sha256(adr)}]
        blocks_test.write_json(selection_path, selection); blocks_test.write_json(map_path, architecture)
        blocks_test.refresh_registration(selection_path, map_path)
        original = {path: path.read_bytes() for path in (selection_path, map_path, adr)}
        project = self.root / selection['targets'][0]['path']
        project.unlink()
        def validate():
            result = subprocess.run([sys.executable, str(blocks_test.RESOLVER), 'validate-accepted',
                '--target', str(self.root), '--require-placement-provenance'], capture_output=True, text=True, timeout=45)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        validate()
        project.write_text('<Project Sdk="Microsoft.NET.Sdk" />\n')
        (self.root / 'Directory.Build.props').write_text('<Project />\n')
        validate()
        self.assertTrue(all(path.read_bytes() == payload for path, payload in original.items()))

    def test_legacy_image_build_requires_review_without_mutating_accepted_selection(self):
        target = self.target('host-image', 'Dockerfile')
        del target['placement']
        before = copy.deepcopy(target)
        with self.assertRaisesRegex(self.blocks.ResolverError, 'review legacy'):
            self.validate(target)
        self.assertEqual(target, before)

    def test_bootstrap_projects_existing_release_section_and_rejects_missing_authority(self):
        with self.assertRaisesRegex(self.context.ContextError, 'before dispatch'):
            self.context.runtime_release_projection(self.root, self.intake)
        relative = '.specify/extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md'
        source = ROOT / 'extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md'
        path = self.root / relative
        path.parent.mkdir(parents=True)
        shutil.copyfile(source, path)
        first = self.context.runtime_release_projection(self.root, self.intake)
        self.assertIn('nuplane.settings.json', first['contract'])
        self.assertIn('not a consumer Docker image', first['contract'])
        self.assertEqual(first['sha256'], self.blocks.raw_sha256(path))
        path.write_text(path.read_text(encoding='utf-8').replace('One application release produces', 'Every application release produces'), encoding='utf-8')
        second = self.context.runtime_release_projection(self.root, self.intake)
        self.assertNotEqual(first['sha256'], second['sha256'])
        self.assertIn('Every application release produces', second['contract'])


if __name__ == '__main__':
    unittest.main()
