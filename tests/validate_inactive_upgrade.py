"""Bounded inactive-history upgrades, reviewed transport and checkout conversion."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'extensions/program-kit-governance/scripts'),
               str(ROOT/'extensions/program-kit-dotnet/scripts')]
import consumer_upgrade_workspace as workspace
import consumer_upgrade as flow
import inactive_history as history
import dotnet_sync
import validate_building_blocks as fixture
import validate_bootstrap_semantics as semantics
import architecture_map
from owned_fixture import FixtureDirectory

blocks = fixture.load_module(ROOT/'extensions/program-kit-building-blocks/scripts/building_blocks.py')


def write(root, relative, value):
    path = root/relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2)+'\n').encode() if isinstance(value, (dict, list)) else value)
    return path


def inventory(root):
    return {p.relative_to(root).as_posix(): history.sha(p) for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}


class InactiveUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.directory = FixtureDirectory(native=True)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)/'consumer'
        self.root.mkdir()
        catalog = blocks.load_json(fixture.CATALOG)
        selection, model = fixture.accepted_fixture(blocks, self.root, catalog, 'api_baseline')
        (self.root/'src/Test.Feature/Test.Feature.csproj').unlink()
        adr = write(self.root, 'docs/architecture/decisions/historical.md', b'# Historical Accepted decision\n')
        value = blocks.load_json(model)
        value['decisions'][0].update(path=adr.relative_to(self.root).as_posix(), sha256=history.sha(adr))
        value['elements'] = [{'id': 'owner', 'ownership': 'Consumer', 'decision_refs': ['use-building-blocks']}]
        write(self.root, model.relative_to(self.root), value)
        selection_value = blocks.load_json(selection)
        selection_value['targets'][0]['placement'] = {'state': 'observed', 'owner': 'owner',
            'decisionIds': ['use-building-blocks'], 'rationale': 'Historical observed file was intentionally withdrawn.'}
        write(self.root, history.SELECTION, selection_value)
        fixture.refresh_registration(selection, model)
        write(self.root, '.program-kit/managed.json', {'schemaVersion': 2, 'programKitVersion': '0.13.2',
            'webProfile': 'bff-cookie', 'persistenceProfile': 'none', 'files': {}})
        write(self.root, 'withdrawal.txt', b'Fictional reviewed withdrawal; no new architecture acceptance.\n')
        intake_root = self.root/'reviewed-intake'
        intent = write(intake_root, 'docs/architecture/project-intent.md', b'# Fictional calculator intent\n')
        fresh = semantics.semantic_model(intent)
        write(intake_root, 'docs/architecture/architecture-map.json', fresh)
        write(intake_root, 'docs/architecture/workspace.dsl', architecture_map.StructurizrDslExporter().export(fresh).encode())
        write(intake_root, 'docs/architecture/bootstrap-intake.json', semantics.intake_for(intake_root, fresh, 'confirmed'))
        inputs = {p: h for p, h in inventory(self.root).items() if p.startswith(('docs/architecture/', 'reviewed-intake/')) or p == 'withdrawal.txt'}
        for name in [history.LOCK, history.COMPOSITION, history.PROFILE, 'docs/architecture/bootstrap-decisions.json',
                     '.specify/governance/migration-completion.json', 'eng/.config/dotnet-tools.json', 'eng/ProgramKit.Packages.props',
                     'eng/ProgramKit.Foundation.props']:
            inputs[name] = history.sha(self.root/name)
        for target in selection_value['targets']:
            inputs[target['path']] = history.sha(self.root/target['path'])
        self.contract = {'schemaVersion': 1, 'scope': 'tooling-only-inactive-history',
            'rationale': 'Synthetic reviewed withdrawal; preserve originals.', 'intakeRoot': 'reviewed-intake',
            'withdrawalEvidence': ['withdrawal.txt'], 'historicalSubjects': {}, 'historicalPersistence': None,
            'retainedApplicationTooling': {}, 'inputs': inputs}
        self.bind()

    def bind(self):
        path = write(self.root, 'history.json', self.contract)
        self.binding = {'declaration': 'history.json', 'declarationSha256': history.sha(path)}

    def validate(self):
        return history.validate(self.root, 'history.json', self.binding['declarationSha256'], blocks)

    def command(self, *extra):
        result = subprocess.run([sys.executable, str(ROOT/'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
            '--target', str(self.root), '--profile-selected', '--upgrade-existing', '--json',
            *history.arguments(self.binding), *extra], capture_output=True, text=True)
        self.assertIn(result.returncode, (0, 1), result.stdout + result.stderr)
        return result

    def test_active_guards_and_explicit_tooling_apply_are_separate_and_idempotent(self):
        before = inventory(self.root)
        with self.assertRaisesRegex(ValueError, 'PKM003'):
            dotnet_sync.selected_web_profile(self.root, 'auto')
        with self.assertRaisesRegex(ValueError, 'PKB306'):
            blocks.validate_placements(self.root, blocks.load_json(self.root/history.SELECTION))
        result = self.validate()
        self.assertFalse(result['designAcceptanceEstablished'])
        self.assertEqual(before, inventory(self.root))
        preview = json.loads(self.command('--check').stdout)
        self.assertTrue(preview['actions'])
        self.assertTrue(all(row['path'].startswith('eng/') and Path(row['path']).suffix in {'.py','.ps1','.psm1','.sh'} for row in preview['actions']))
        self.command('--plan-digest', preview['planDigest'])
        self.assertEqual(0, self.command('--check').returncode)
        retained = {p: h for p, h in before.items() if p != '.program-kit/managed.json'}
        self.assertEqual(retained, {p: history.sha(self.root/p) for p in retained})
        self.assertFalse((self.root/history.COMPOSITION).exists())
        with self.assertRaisesRegex(ValueError, 'PKM003'):
            dotnet_sync.selected_web_profile(self.root, 'auto')

    def test_changed_missing_and_incomplete_history_reject_without_writes(self):
        write(self.root, 'withdrawal.txt', b'changed\n')
        before = inventory(self.root)
        with self.assertRaisesRegex(ValueError, 'history input changed'):
            self.validate()
        self.assertEqual(before, inventory(self.root))
        write(self.root, 'withdrawal.txt', b'Fictional reviewed withdrawal; no new architecture acceptance.\n')
        del self.contract['inputs'][history.LOCK]
        self.bind()
        with self.assertRaisesRegex(ValueError, 'omits required originals'):
            self.validate()

    def test_materialized_targets_unmanaged_dependencies_and_composition_cannot_hide(self):
        for name, content in [('src/Test.Feature/Test.Feature.csproj', b'<Project/>'),
                              (history.COMPOSITION, b'{}'),
                              ('other/new.csproj', b'<Project/>')]:
            path = write(self.root, name, content)
            before = inventory(self.root)
            with self.assertRaisesRegex(ValueError, 'PKU149'):
                self.validate()
            self.assertEqual(before, inventory(self.root))
            path.unlink()
        write(self.root, 'unmanaged.props', b'<Project><ItemGroup><PackageVersion Include="Orbyss.Foundation.DomainEvents" Version="1.0.0"/></ItemGroup></Project>')
        with self.assertRaisesRegex(ValueError, 'PKB405'):
            self.validate()

    def test_unconfirmed_intake_and_changed_declaration_cannot_acquire_authority(self):
        with self.assertRaisesRegex(ValueError, 'declaration changed'):
            history.validate(self.root, 'history.json', '0'*64, blocks)
        path = self.root/'reviewed-intake/docs/architecture/bootstrap-intake.json'
        value = json.loads(path.read_text()); value['status'] = 'draft'
        write(self.root, path.relative_to(self.root), value)
        self.contract['inputs'][path.relative_to(self.root).as_posix()] = history.sha(path)
        self.bind()
        with self.assertRaisesRegex(RuntimeError, 'not confirmed'):
            self.validate()


class WorkspaceRepairTests(unittest.TestCase):
    def setUp(self):
        self.directory = FixtureDirectory(native=True)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)/'consumer'; self.root.mkdir()

    def test_exact_reviewed_arguments_reject_missing_changed_and_retry_substitution(self):
        contract = write(self.root, 'cases.json', {'schemaVersion': 1})
        declaration = write(self.root, 'repairs.json', {'contract': 'cases.json', 'contractSha256': history.sha(contract)})
        extra = ['--local-repairs','repairs.json','--local-repairs-sha256',history.sha(declaration)]
        binding = workspace.reviewed_options(self.root, extra)
        self.assertEqual(extra, binding['arguments'])
        self.assertEqual(binding, workspace.reviewed_options(self.root, extra, binding))
        for invalid in [extra[:2], extra[:-1]+['0'*64], []]:
            with self.assertRaises(ValueError): workspace.reviewed_options(self.root, invalid, binding)
        contract.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'case contract changed'):
            workspace.reviewed_options(self.root, extra, binding)

    def test_install_passes_arguments_records_failure_and_retry_reexecutes(self):
        declaration = write(self.root, 'repairs.json', {'contract': 'cases.json', 'contractSha256': history.sha(write(self.root,'cases.json',{}))})
        extra = ['--local-repairs','repairs.json','--local-repairs-sha256',history.sha(declaration)]
        state = {'workspace': {'releaseInputsSha256':'exact'}, 'targetVersion': '0.14.0'}
        commands = []
        def execute(command, *args, **kwargs):
            commands.append(command); return 2 if len(commands) == 1 else 0
        with patch.object(flow,'load',return_value=state), patch.object(flow,'save'), \
             patch.object(workspace.updater,'validate_release',return_value='0.14.0'), \
             patch.object(workspace.updater,'release_fingerprint',return_value='exact'), \
             patch.object(flow,'installation_inputs',return_value={}), patch.object(flow,'capture',return_value={}), \
             patch('compatibility_process.run',side_effect=execute):
            self.assertEqual(2, workspace.install(self.root,ROOT,extra)['updaterExitCode'])
            self.assertEqual(extra, state['updaterOptions']['arguments'])
            with self.assertRaises(ValueError): workspace.install(self.root,ROOT,[])
            self.assertEqual(0, workspace.install(self.root,ROOT,extra)['updaterExitCode'])
        self.assertEqual(2,len(commands))
        self.assertTrue(all(command[-len(extra):] == extra for command in commands))

    def test_activation_carries_missing_review_artifacts_and_refuses_existing_conflicts(self):
        destination = self.root.parent/'destination'; destination.mkdir()
        module = write(self.root,'artifacts/review/cases.py',b'# Fictional reviewed module, not executed by transport\n')
        contract = write(self.root,'artifacts/review/cases.json',{'modules':[{'path':'artifacts/review/cases.py','sha256':history.sha(module)}]})
        declaration = write(self.root,'artifacts/review/repairs.json',{'contract':'artifacts/review/cases.json','contractSha256':history.sha(contract)})
        extra = ['--local-repairs','artifacts/review/repairs.json','--local-repairs-sha256',history.sha(declaration)]
        selection = workspace.reviewed_options(self.root,extra)
        pending = workspace.transfer_reviewed_inputs(self.root,destination,selection)
        self.assertEqual(3,len(pending)); self.assertFalse((destination/'artifacts').exists())
        workspace.transfer_reviewed_inputs(self.root,destination,selection,apply=True)
        self.assertEqual(selection,workspace.reviewed_options(destination,extra,selection))
        path = write(destination,'artifacts/review/cases.py',b'conflicting review\n')
        with self.assertRaisesRegex(ValueError,'Destination reviewed input conflicts'):
            workspace.transfer_reviewed_inputs(self.root,destination,selection,apply=True)
        self.assertEqual(b'conflicting review\n',path.read_bytes())

    def test_core_utf8_inventory_uses_exact_existing_owner_and_rejects_other_edits(self):
        import ensure_utf8
        flow.git(self.root,'init')
        flow.git(self.root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                 'commit','--allow-empty','-m','Known fixture baseline')
        relative = '.specify/scripts/python/common.py'
        original = b'from __future__ import annotations\nprint("fixture")\n'
        path = write(self.root,relative,ensure_utf8.hardened(original.decode()).encode())
        write(self.root,'.specify/integrations/speckit.manifest.json',{'integration':'speckit','version':'1.2.0',
              'files':{relative:hashlib.sha256(original).hexdigest()}})
        before = inventory(self.root)
        observed = flow.inventory(self.root)
        self.assertNotIn(relative,observed['customizations'])
        self.assertEqual('exact-native-utf8-transformation',observed['ownedInstallation'][relative]['baselineOwner'])
        self.assertEqual(before,inventory(self.root))
        path.write_bytes(path.read_bytes()+b'# unrelated customization\n')
        self.assertIn(relative,flow.inventory(self.root)['customizations'])

    def test_preparation_repairs_only_blob_authenticated_newlines_after_all_conflicts_checked(self):
        flow.git(self.root,'init')
        flow.git(self.root,'config','core.autocrlf','false')
        write(self.root,'owned.txt',b'one\ntwo\n')
        flow.git(self.root,'add','owned.txt')
        flow.git(self.root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','original')
        archive = self.root.parent/'archive'
        hashes = workspace.snapshot(self.root,archive,['owned.txt'])
        write(self.root,'owned.txt',b'one\r\ntwo\r\n')
        fixed = workspace.reproduce(archive,self.root,hashes)
        self.assertEqual(['owned.txt'],[row['path'] for row in fixed])
        self.assertEqual(b'one\ntwo\n',(self.root/'owned.txt').read_bytes())
        write(self.root,'owned.txt',b'custom\r\n')
        with self.assertRaisesRegex(ValueError,'conflicts'):
            workspace.reproduce(archive,self.root,hashes)
        self.assertEqual(b'custom\r\n',(self.root/'owned.txt').read_bytes())
        write(archive,'owned.txt',b'not committed\n')
        write(self.root,'owned.txt',b'not committed\r\n')
        with self.assertRaisesRegex(ValueError,'conflicts'):
            workspace.reproduce(archive,self.root,{'owned.txt': history.sha(archive/'owned.txt')})

    def test_retained_composition_pins_keep_exact_receipts_and_selected_versions(self):
        import dependency_audit as audit
        catalog = blocks.load_json(fixture.CATALOG)
        package = next(p for p in catalog['packages'].values() if p['ecosystem'] == 'nuget')
        relative = 'eng/ProgramKit.Foundation.props'
        path = write(self.root,relative, ('<Project><ItemGroup><PackageVersion Include="' + package['packageId'] + '" Version="'
                                        + package['version'] + '"/></ItemGroup></Project>').encode())
        def receipt():
            write(self.root,'.program-kit/managed.json',{'files':{relative:{'ownership':'managed','contribution':'foundation',
                'sourceIdentity':'../../scripts/foundation_composition.py','lastWrittenHash':history.sha(path),'templateHash':history.sha(path)}}})
        receipt()
        self.assertEqual({path.resolve()},audit.inactive_composition_pins(self.root,catalog))
        path.write_bytes(path.read_bytes().replace(package['version'].encode(),b'0.0.0'))
        with self.assertRaisesRegex(ValueError,'ownership receipt'): audit.inactive_composition_pins(self.root,catalog)
        receipt()
        with self.assertRaisesRegex(ValueError,'selected dependency catalog'): audit.inactive_composition_pins(self.root,catalog)

    def test_historical_ef_tool_is_exact_and_does_not_relax_active_ownership(self):
        import dependency_audit as audit
        from types import SimpleNamespace
        original = {'version':1,'isRoot':True,'tools':{'orbyss.foundation.openapi.exporter':{'version':'0.2.6','commands':['orbyss-foundation-openapi-export']}}}
        template = write(self.root,'.specify/extensions/program-kit-dotnet/templates/dotnet/files/eng/.config/dotnet-tools.json',original)
        relative = 'eng/.config/dotnet-tools.json'
        actual = copy.deepcopy(original)
        actual['tools']['dotnet-ef'] = {'version':'10.0.13','commands':['dotnet-ef']}
        path = write(self.root,relative,actual)
        write(self.root,'.program-kit/managed.json',{'files':{relative:{'ownership':'managed','sourceIdentity':'files/'+relative,
            'lastWrittenHash':history.sha(template),'templateHash':history.sha(template)}}})
        profile = SimpleNamespace(render=lambda root,relative,content: content)
        persistence = SimpleNamespace(resolve=lambda root: {},effective=lambda s:s,pins=lambda s,t:{})
        def provider(name): return profile if name.endswith('dependency_profile.py') else persistence
        with patch('repository_sync.provider',side_effect=provider):
            with self.assertRaisesRegex(ValueError,'ownership hash changed'): audit.engineering_outputs(self.root)
            self.assertEqual({path.resolve()},audit.engineering_outputs(self.root,inactive_tool_pin='10.0.13'))
            with self.assertRaises(ValueError): audit.engineering_outputs(self.root,inactive_tool_pin='10.0.14')
            actual['tools']['unreviewed'] = {'version':'1.0.0'}
            write(self.root,relative,actual)
            with self.assertRaises(ValueError): audit.engineering_outputs(self.root,inactive_tool_pin='10.0.13')


if __name__ == '__main__':
    unittest.main()
