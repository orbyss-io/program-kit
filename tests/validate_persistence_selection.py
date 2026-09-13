"""Exercise consumer persistence intent, multiple owners and non-destructive shared sync."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import persistence_selection as persistence
import repository_sync as sync
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files'


class PersistenceTests(unittest.TestCase):
    def test_shared_schema_resolves_owner_and_feature_admission_contracts(self):
        from json_schema import validate_value
        location = ROOT / 'extensions/program-kit-governance/references/bootstrap-decisions.schema.json'
        owner = self.owner()
        schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$ref': 'persistence.schema.json#/$defs/owners'}
        result = validate_value([owner], schema, location)
        self.assertTrue(result['valid'], result)
        admission = {key: value for key, value in owner.items() if key not in {'owner', 'storage', 'profile'}}
        schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$ref': 'persistence.schema.json#/$defs/admission'}
        result = validate_value(admission, schema, location)
        self.assertTrue(result['valid'], result)
        admission['profile'] = 'ef-sqlite'
        self.assertFalse(validate_value(admission, schema, location)['valid'])

    def test_untouched_old_scaffold_upgrades_but_customized_scaffold_requires_correction(self):
        self.select(self.owner())
        command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                   '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
                   '--building-block-sources-approved', '--web-profile', 'none']
        def run():
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        run()
        central = self.root / 'Directory.Packages.props'
        old = b'<Project><PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup></Project>\n'
        managed = self.root / '.program-kit/managed.json'
        original_state = json.loads(managed.read_text())
        for customized in (False, True):
            state = copy.deepcopy(original_state)
            previous = state['files']['Directory.Packages.props']
            previous['baselineHash'] = previous['lastWrittenHash'] = hashlib.sha256(old).hexdigest()
            managed.write_text(json.dumps(state))
            content = old.replace(b'</Project>', b'<!-- consumer policy --></Project>') if customized else old
            central.write_bytes(content)
            run()
            if customized:
                self.assertEqual(content, central.read_bytes())
                self.assertTrue(persistence.coherence(self.root, persistence.resolve(self.root), TEMPLATE))
            else:
                self.assertIn(b'ProgramKit.Persistence.props', central.read_bytes())
                self.assertEqual([], persistence.coherence(self.root, persistence.resolve(self.root), TEMPLATE))

    def test_supervisor_provisioning_omits_unused_testcontainers_and_pins_ef_tool(self):
        owner = self.owner(); owner['testProvisioning'] = 'supervisor'
        selection = self.select(owner)
        self.assertNotIn('Testcontainers.PostgreSql', persistence.pins(selection, TEMPLATE))
        command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                   '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
                   '--building-block-sources-approved', '--web-profile', 'none']
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        tools = json.loads((self.root / '.program-kit/eng/.config/dotnet-tools.json').read_text())['tools']
        self.assertEqual(persistence.pins(selection, TEMPLATE)['Microsoft.EntityFrameworkCore.Design'], tools['dotnet-ef']['version'])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='persistence-selection-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet']})

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def owner(self, name='Reservations', profile='auto', admitted=True):
        path = self.root / 'docs/architecture/persistence.md'
        path.write_text('Status: Accepted\nOwned reservation transaction, stable replay identity, controlled migrations and real-provider tests.')
        return {'owner': name, 'storage': 'server-relational', 'profile': profile,
                'status': 'admitted' if admitted else 'proposed', 'capability': name + '.Admission',
                'providerProject': f'src/{name}.Persistence/{name}.Persistence.csproj',
                'testProjects': [f'tests/{name}.Tests/{name}.Tests.csproj'], 'checkIds': [name + '.rollback'],
                'admission': {key: ['docs/architecture/persistence.md'] for key in persistence.ADMISSIONS}}

    def select(self, *owners):
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet'], 'persistence': list(owners)})
        return persistence.resolve(self.root)

    def test_no_store_and_explicit_none_do_not_install_provider(self):
        self.assertEqual('none', persistence.resolve(self.root)['summary'])
        selection = self.select({'owner': 'Reports', 'storage': 'none', 'profile': 'auto', 'status': 'admitted'})
        self.assertEqual({}, persistence.pins(selection, TEMPLATE))
        self.assertEqual([], selection['blockers'])

    def test_inherited_and_explicit_postgres_agree_before_materialization(self):
        for profile in ('auto', 'ef-postgresql'):
            self.select(self.owner(profile=profile))
            for phase in ('bootstrap', 'planning', 'implementation-setup'):
                context = sync.context(self.root, phase, None)
                self.assertEqual('ef-postgresql', context['persistenceProfile'])
                self.assertFalse((self.root / '.program-kit').exists())

    def test_unassigned_legacy_intent_remains_proposed_and_blocks_admission(self):
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet', 'ef-postgresql']})
        selection = persistence.resolve(self.root)
        self.assertEqual('ef-postgresql', selection['summary'])
        self.assertTrue(selection['blockers'])
        self.assertEqual({}, persistence.pins(selection, TEMPLATE))

    def test_pending_admission_and_missing_evidence_are_not_installed(self):
        selection = self.select(self.owner(admitted=False))
        self.assertEqual('ef-postgresql', selection['summary'])
        self.assertEqual({}, persistence.pins(selection, TEMPLATE))
        owner = self.owner(); owner['admission']['atomicity'] = ['missing.md']
        self.assertTrue(any('atomicity' in e for e in self.select(owner)['blockers']))

    def test_feature_admission_does_not_rewrite_approved_bootstrap_intent(self):
        owner = self.owner()
        self.select({'owner': 'Reservations', 'storage': 'server-relational', 'profile': 'auto', 'status': 'proposed'})
        approved = (self.root / 'docs/architecture/bootstrap-decisions.json').read_bytes()
        admission = {key: value for key, value in owner.items() if key not in {'owner', 'storage', 'profile'}}
        self.write('.specify/feature.json', {'feature_directory': 'specs/001-reserve'})
        self.write('specs/001-reserve/artifact-ownership.json', {'persistenceOwners': ['Reservations'],
                   'persistenceAdmissions': {'Reservations': admission}})
        selection = persistence.resolve(self.root)
        self.assertEqual([], selection['blockers'])
        self.assertTrue(persistence.pins(selection, TEMPLATE))
        self.assertEqual(approved, (self.root / 'docs/architecture/bootstrap-decisions.json').read_bytes())
        admission['profile'] = 'ef-sqlite'
        self.write('specs/001-reserve/artifact-ownership.json', {'persistenceOwners': ['Reservations'], 'persistenceAdmissions': {'Reservations': admission}})
        with self.assertRaisesRegex(ValueError, 'cannot override canonical'):
            persistence.resolve(self.root)

    def test_unrelated_future_owner_does_not_block_the_current_feature(self):
        first = self.owner(); future = self.owner('FutureReporting', admitted=False)
        self.select(first, future)
        self.write('specs/001-reserve/artifact-ownership.json', {'persistenceOwners': ['Reservations']})
        self.assertEqual([], persistence.resolve(self.root, 'specs/001-reserve')['blockers'])
        self.assertTrue(persistence.resolve(self.root)['blockers'])
        self.select(first, self.owner('FutureReporting'))
        selection = persistence.resolve(self.root, 'specs/001-reserve')
        shutil.copytree(TEMPLATE / '.program-kit/eng', self.root / '.program-kit/eng')
        (self.root / persistence.AGGREGATE).write_bytes(persistence.render(selection, TEMPLATE))
        (self.root / 'Directory.Packages.props').write_text('<Project><Import Project=".program-kit/eng/ProgramKit.Persistence.props" /></Project>')
        errors = persistence.coherence(self.root, selection, TEMPLATE, materialized=True)
        self.assertTrue(any('Reservations' in error for error in errors))
        self.assertFalse(any('FutureReporting' in error for error in errors))

    def test_later_accepted_override_preserves_bootstrap_and_survives_upgrade(self):
        self.select({'owner': 'Reservations', 'storage': 'server-relational', 'profile': 'auto', 'status': 'proposed'})
        before = (self.root / 'docs/architecture/bootstrap-decisions.json').read_bytes()
        owner = self.owner(profile='ef-sqlite')
        admission = {k: v for k, v in owner.items() if k not in {'owner', 'storage', 'profile'}}
        admission['providerOverride'] = {'profile': 'ef-sqlite', 'authority': 'docs/architecture/persistence.md'}
        self.write('specs/002-change/artifact-ownership.json', {'persistenceOwners': ['Reservations'], 'persistenceAdmissions': {'Reservations': admission}})
        selection = persistence.resolve(self.root, 'specs/002-change')
        self.assertEqual([], selection['blockers'])
        self.assertEqual('ef-sqlite', selection['summary'])
        self.write('.program-kit/managed.json', {'persistenceProfile': 'ef-sqlite', 'persistenceOwners': selection['owners']})
        self.assertEqual('ef-sqlite', persistence.resolve(self.root)['summary'])
        self.assertEqual(before, (self.root / 'docs/architecture/bootstrap-decisions.json').read_bytes())
        (self.root / 'docs/architecture/persistence.md').write_text('Status: Proposed\nUnaccepted transition')
        self.assertTrue(persistence.resolve(self.root)['blockers'])

    def test_multiple_providers_deduplicate_common_pins(self):
        selection = self.select(self.owner(), self.owner('Catalog', 'ef-sqlite'))
        root = ET.fromstring(persistence.render(selection, TEMPLATE))
        names = [node.attrib['Include'] for node in root.iter('PackageVersion')]
        self.assertEqual(1, names.count('Microsoft.EntityFrameworkCore'))
        self.assertIn('Npgsql.EntityFrameworkCore.PostgreSQL', names)
        self.assertIn('Microsoft.EntityFrameworkCore.Sqlite', names)
        self.assertEqual('mixed', selection['summary'])

    def test_custom_pin_conflict_is_rejected(self):
        custom = self.owner('Other', 'custom')
        custom['packages'] = {'Microsoft.EntityFrameworkCore': '9.0.0'}
        custom['packageAssignments'] = {'provider': ['Microsoft.EntityFrameworkCore'], 'tests': []}
        with self.assertRaisesRegex(ValueError, 'conflicting shared pin'):
            persistence.render(self.select(self.owner(), custom), TEMPLATE)

    def test_evaluated_graph_catches_disabled_items_overrides_and_core_leakage(self):
        selection = self.select(self.owner())
        owner = selection['owners'][0]
        pins = persistence.pins(selection, TEMPLATE)
        evaluated = {}
        for project in [owner['providerProject'], *owner['testProjects']]:
            references = [{'Identity': name, 'PrivateAssets': 'all'} for name in persistence.project_packages(owner, project, TEMPLATE)]
            evaluated[project] = {'Properties': {'ManagePackageVersionsCentrally': 'true'}, 'Items': {
                'PackageReference': references, 'PackageVersion': [{'Identity': name, 'Version': version} for name, version in pins.items()]}}
        persistence.validate_evaluated(selection, TEMPLATE, evaluated)
        bad = copy.deepcopy(evaluated); bad[owner['providerProject']]['Items']['PackageReference'] = []
        with self.assertRaisesRegex(ValueError, 'assignment/pin'):
            persistence.validate_evaluated(selection, TEMPLATE, bad)
        bad = copy.deepcopy(evaluated); bad[owner['providerProject']]['Items']['PackageReference'][0]['VersionOverride'] = '9.0.0'
        with self.assertRaisesRegex(ValueError, 'assignment/pin'):
            persistence.validate_evaluated(selection, TEMPLATE, bad)
        bad = copy.deepcopy(evaluated); bad['src/Core/Core.csproj'] = {'Items': {'PackageReference': [{'Identity': 'Microsoft.EntityFrameworkCore'}]}}
        with self.assertRaisesRegex(ValueError, 'escape'):
            persistence.validate_evaluated(selection, TEMPLATE, bad)

    def test_upgrade_preserves_installed_owner_without_new_choice(self):
        selection = self.select(self.owner(profile='ef-sqlite'))
        self.write('.program-kit/managed.json', {'persistenceProfile': 'ef-sqlite', 'persistenceOwners': selection['owners']})
        self.write('docs/architecture/bootstrap-decisions.json', {'selected_profiles': ['dotnet']})
        self.assertEqual('ef-sqlite', sync.context(self.root, 'upgrade', None)['persistenceProfile'])

    def test_unapproved_switch_or_removal_keeps_installed_pins(self):
        original = self.select(self.owner(profile='ef-sqlite'))
        self.write('.program-kit/managed.json', {'persistenceProfile': 'ef-sqlite', 'persistenceOwners': original['owners']})
        for owners in ([self.owner()], []):
            changed = self.select(*owners)
            self.assertTrue(changed['blockers'])
            self.assertEqual(persistence.render(original, TEMPLATE), persistence.render(changed, TEMPLATE))
        changed_owner = self.owner(); changed_owner['transitionAuthority'] = 'docs/architecture/persistence.md'
        self.assertEqual([], self.select(changed_owner)['blockers'])

    def test_coherence_rejects_missing_import_duplicate_pin_and_unowned_override(self):
        selection = self.select(self.owner())
        shutil.copytree(TEMPLATE / '.program-kit/eng', self.root / '.program-kit/eng')
        (self.root / persistence.AGGREGATE).write_bytes(persistence.render(selection, TEMPLATE))
        central = self.root / 'Directory.Packages.props'
        central.write_text('<Project />')
        self.assertTrue(any('central pin' in e for e in persistence.coherence(self.root, selection, TEMPLATE)))
        central.write_text('<Project><Import Project=".program-kit/eng/ProgramKit.Persistence.props" /></Project>')
        self.assertEqual([], persistence.coherence(self.root, selection, TEMPLATE))
        self.assertTrue(any('create owned' in e for e in persistence.coherence(self.root, selection, TEMPLATE, materialized=True)))
        central.write_text(central.read_text().replace('</Project>', '<ItemGroup><PackageVersion Include="Microsoft.EntityFrameworkCore" Version="9.0.0" /></ItemGroup></Project>'))
        self.assertTrue(any('central package graph' in e for e in persistence.coherence(self.root, selection, TEMPLATE)))

    def test_fresh_sync_repeat_and_upgrade_preserve_consumer_files(self):
        self.select(self.owner())
        command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                   '--target', str(self.root), '--profile-selected', '--foundation-host-accepted',
                   '--building-block-sources-approved', '--web-profile', 'none']
        for attempt in range(2):
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        central = self.root / 'Directory.Packages.props'
        central.write_text(central.read_text().replace('<!-- Consumer-owned', '<!-- Kept custom policy. -->\n  <!-- Consumer-owned'))
        expected = central.read_bytes()
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(expected, central.read_bytes())
        self.assertEqual('ef-postgresql', sync.context(self.root, 'upgrade', None)['persistenceProfile'])
        selection = persistence.resolve(self.root)
        self.assertEqual([], persistence.coherence(self.root, selection, TEMPLATE))


if __name__ == '__main__':
    unittest.main()
