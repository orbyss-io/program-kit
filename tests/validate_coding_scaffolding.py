"""F4 independent ownership/creation/transaction negatives and source adapter tests."""
from pathlib import Path
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'),
               str(ROOT / 'extensions/program-kit-dotnet/scripts')]
from owned_fixture import FixtureDirectory
import coding_scaffold as scaffold
import reconciliation
import typed_operation


class ScaffoldTests(unittest.TestCase):
    def test_native_preview_needs_real_recipe_inputs_without_lifecycle_or_pattern_receipts(self):
        with FixtureDirectory(native=True) as directory:
            root = Path(directory)
            (root / '.program-kit').mkdir()
            (root / '.program-kit/managed.json').write_bytes(b'{"files":{}}\n')
            eng = root / 'eng'; eng.mkdir()
            roles = {'core':'core', 'runtime':'implementation', 'api':'implementation', 'provider':'provider', 'test':'test'}
            kinds = {'core':'pure-policy', 'runtime':'runtime', 'api':'http', 'provider':'persistence', 'test':'test'}
            declarations = []
            for key, role in roles.items():
                project = root / self.owners[key]
                project.parent.mkdir(parents=True)
                refs = [] if key == 'core' else [self.owners['core']]
                if key == 'test':
                    refs.append(self.owners['runtime'])
                packages = {'api':['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'],
                            'runtime':['Orbyss.Foundation.Execution'],
                            'provider':['Orbyss.Foundation.PostgreSql']}.get(key, [])
                items = ''.join(f'<PackageReference Include="{name}" Version="0.3.10"/>' for name in packages)
                items += ''.join(f'<ProjectReference Include="{os.path.relpath(root / ref, project.parent)}"/>' for ref in refs)
                project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework>'
                    '</PropertyGroup><ItemGroup>' + items + '</ItemGroup></Project>', encoding='utf-8')
                declarations.append({'path':self.owners[key], 'role':role, 'projectReferences':refs,
                    'responsibilities':[{'name':key, 'kind':kinds[key], 'effects':[]}]})
            (eng / 'architecture.json').write_text(json.dumps({'runtimeComposition':{'projects':declarations}}))
            frontend = root / self.owners['frontend']; frontend.mkdir(parents=True)
            (frontend / 'package.json').write_text('{"private":true}\n')
            (eng / 'openapi-contracts.json').write_text('{"contracts":["eng/labels-api.json"]}\n')
            contract = {'generator':{'generatedTypes':self.owners['generatedTypes']},
                        'application':{'directory':self.owners['frontend']}}
            (eng / 'labels-api.json').write_text(json.dumps(contract))
            lock = root / 'src/api/packages.lock.json'
            lock.write_bytes(b'{"version":1,"dependencies":{"net10.0":{}}}\n')
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            plan, outputs = scaffold.preview(root, root / 'specs/001-label', 'typed-label', self.owners)
            self.assertTrue(outputs and all(row['kind']=='create' for row in plan['actions']))
            self.assertFalse(plan['conflicts'])
            self.assertEqual(before, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root / 'docs/architecture').exists(), 'No consumer qualification/approval files are needed')
            for legacy_path in ('src/core/ILabelOperations.cs', 'src/runtime/LabelOperations.cs',
                                'src/provider/PostgreSqlLabelStore.cs', 'src/api/LabelEndpoint.cs'):
                old = root / legacy_path
                old.write_bytes(b'// Preserve independently authored partial legacy adoption.\n')
                preserved = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
                conflict, candidate = scaffold.preview(root, root / 'specs/001-label', 'typed-label', self.owners)
                self.assertIn(legacy_path, [r['path'] for r in conflict['conflicts'] if r.get('kind') == 'legacy-placement'])
                with self.assertRaisesRegex(ValueError, 'consumer source preserved'):
                    scaffold.apply(root, conflict, candidate, conflict['planDigest'])
                self.assertEqual(preserved, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
                old.unlink()
            # A partial legacy file appearing after an inspected preview also
            # rejects the creation path before a nested duplicate is written.
            old = root / 'src/core/ILabelStore.cs'; old.write_bytes(b'// Late authored type.\n')
            with self.assertRaisesRegex(ValueError, 'earlier recipe locations'):
                scaffold.apply(root, plan, outputs, plan['planDigest'])
            self.assertFalse((root / 'src/core/Labels/ILabelStore.cs').exists())
            old.unlink()
            api = root / self.owners['api']
            api.write_text(api.read_text().replace('Version="0.3.10"', 'Version="0.3.7"'))
            rejected = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'qualified Foundation runtime 0.3.10 or later'):
                scaffold.preview(root, root / 'specs/001-label', 'typed-label', self.owners)
            self.assertEqual(rejected, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertIn('Version="0.3.7"', api.read_text(), 'Compatibility rejection must not upgrade consumer pins')
            self.assertEqual(before['src/api/packages.lock.json'], lock.read_bytes())

    def test_emitted_csharp_readability_and_independent_syntax_negatives(self):
        from csharp_readability_check import check
        self.assertEqual(0, check())

    def setUp(self):
        self.owners = {k: f'src/{k}/{k}.csproj' for k in ('core', 'runtime', 'api', 'provider', 'test')}
        self.owners.update(frontend='web/app', generatedTypes='tools/openapi/labels/generated/types.ts')

    def test_exact_source_owner_split_and_generated_client_import(self):
        output = typed_operation.render(self.owners, ROOT / 'extensions')
        self.assertIn('src/core/Labels/ILabelOperations.cs', output)
        self.assertIn('src/runtime/Labels/LabelOperations.cs', output)
        self.assertIn('src/provider/Labels/PostgreSqlLabelStore.cs', output)
        api = output['src/api/Operations/WriteLabel/Endpoint.cs'].decode()
        self.assertIn('ILabelOperations operations', api)
        self.assertNotIn('ILabelStore', api)
        self.assertNotIn('store.WriteAsync', api)
        self.assertIn('RequestAborted', api)
        read = output['src/api/Operations/ReadLabel/Endpoint.cs'].decode()
        self.assertIn('ReadSampleLabel', read)
        self.assertNotIn('MapPost', read)
        self.assertNotIn('MapGet', api)
        self.assertIn('Representation/LabelResponse.cs', '\n'.join(output))
        self.assertIn('src/api/Configuration/LabelApiOptionsAdmission.cs', output)
        self.assertIn(b'../../../tools/openapi/labels/generated/types', output['web/app/src/client.ts'])
        self.assertFalse(any(p.endswith('.csproj') for p in output), 'no hidden project mutations')

    def test_actual_emitted_browser_adapter_admits_runtime_values(self):
        output = typed_operation.render(self.owners, ROOT / 'extensions')
        with FixtureDirectory() as directory:
            root = Path(directory)
            source = root / 'client.ts'
            source.write_bytes(output['web/app/src/client.ts'])
            probe = ROOT / 'tests/fixtures/typed-operation-client/probe.mjs'
            result = subprocess.run(['node', str(probe), str(source)], cwd=root,
                capture_output=True, text=True, encoding='utf-8', timeout=30)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn('EMITTED_CLIENT_VALID_TOLERANT_AND_BOUNDARY_ADMISSION_PASSED', result.stdout)

    def test_actual_emitted_native_owners_and_outer_deadline(self):
        from typed_operation_native_check import check
        self.assertEqual(0, check())

    def test_actual_api_options_are_observed_at_native_shell_activation(self):
        from typed_operation_native_check import check_api_options_activation
        self.assertEqual(0, check_api_options_activation())

    def test_cold_contract_mode_rejects_ignored_preparation_or_comparison(self):
        for arguments in (['--prepare-only'], ['--prepare-oasdiff'], ['--oasdiff', 'absent-tool']):
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, str(ROOT / 'tests/validate_typed_operation.py'),
                    '--export-client-only', *arguments], cwd=ROOT, capture_output=True,
                    text=True, encoding='utf-8', timeout=10)
                self.assertEqual(2, result.returncode)
                self.assertIn('--export-client-only excludes comparison/tool preparation modes', result.stderr)

    def test_submitted_commands_and_escaping_paths_are_not_adapters(self):
        for change in ({'command': 'anything'}, {'api': '../outside.csproj'}, {'runtime': self.owners['api']},
                       {'frontend': 'C:/private'}, {'generatedTypes': 'schema.json'}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'PKS300'):
                typed_operation.render({**self.owners, **change}, ROOT / 'extensions')

    def test_native_contracts_must_belong_to_the_actual_consuming_owner(self):
        api=[{'id':p,'version':'0.3.10'} for p in ('Orbyss.Foundation.Json.AspNetCore','Orbyss.Foundation.Web.ProblemDetails')]
        provider=[{'id':'Orbyss.Foundation.PostgreSql','version':'0.3.10'}]
        runtime=[{'id':'Orbyss.Foundation.Execution','version':'0.3.10'}]
        projects={self.owners['api']:{'packages':api},self.owners['provider']:{'packages':provider},
                  self.owners['runtime']:{'packages':runtime}}
        scaffold.native_contracts(projects,self.owners)
        with self.assertRaisesRegex(ValueError,'neighboring package'):
            scaffold.native_contracts({self.owners['api']:{'packages':[]},self.owners['provider']:{'packages':api+provider}},self.owners)
        for identity in ('Orbyss.Foundation.Json.AspNetCore','Orbyss.Foundation.Web.ProblemDetails'):
            with self.subTest(owner=identity):
                old=[{**p,'version':'0.3.7'} if p['id']==identity else p for p in api]
                with self.assertRaises(ValueError):
                    scaffold.native_contracts({**projects,self.owners['api']:{'packages':old}},self.owners)

    def test_revised_recipe_requires_stable_qualified_0310_runtime_without_changing_inputs(self):
        identities = {'api': ['Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'],
                      'provider': ['Orbyss.Foundation.PostgreSql'], 'runtime': ['Orbyss.Foundation.Execution']}
        for version in ('0.3.5', '0.3.6', '0.3.7', '0.3.8', '0.3.9', '0.3.10-preview.1', '0.3', '', None, '0.3.10', '0.3.11', '0.4.0'):
            with self.subTest(version=version):
                projects = {self.owners[owner]: {'packages': [{'id': identity, 'version': version} for identity in names]}
                            for owner, names in identities.items()}
                before = json.dumps(projects, sort_keys=True)
                if version in ('0.3.10', '0.3.11', '0.4.0'):
                    scaffold.native_contracts(projects, self.owners)
                else:
                    with self.assertRaisesRegex(ValueError, 'qualified Foundation runtime 0.3.10 or later'):
                        scaffold.native_contracts(projects, self.owners)
                self.assertEqual(before, json.dumps(projects, sort_keys=True))

    def test_route_requires_qualified_adapter_and_source_inputs(self):
        registry = {'codingUnits': [{'id': 'x', 'pattern': {'semanticId': 'typed-label', 'inputs': []}}]}
        units = [{'id': 'x', 'recipes': [typed_operation.RECIPE]}]
        scaffold.routes(units, registry)
        self.assertFalse(units[0]['realization']['available'])
        self.assertIn('program-kit-dotnet/scripts/typed_operation.py', units[0]['realization']['missingQualifiedInputs'])
        units[0]['recipes'] = []
        units[0].pop('realization')
        scaffold.routes(units, registry)
        self.assertNotIn('realization', units[0])

    def test_creation_is_consumer_owned_and_idempotent(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / '.program-kit').mkdir()
            state = b'{"files":{},"authored":"unchanged"}\n'
            (root / '.program-kit/managed.json').write_bytes(state)
            plan = {'planDigest': 'p', 'conflicts': [], 'actions': [
                {'path': 'src/Operation.cs', 'kind': 'create', 'expectedHash': None}]}
            result = scaffold.apply(root, plan, {'src/Operation.cs': b'authored application'}, 'p')
            self.assertEqual(['src/Operation.cs'], result['created'])
            self.assertEqual(state, (root / '.program-kit/managed.json').read_bytes())
            plan['actions'][0]['kind'] = 'unchanged'
            rerun = scaffold.apply(root, plan, {}, 'p')
            self.assertIsNone(rerun['transactionId'])
            self.assertEqual(b'authored application', (root / 'src/Operation.cs').read_bytes())

    def test_stale_preview_conflict_and_intervening_file_preserve_all_source(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / '.program-kit').mkdir()
            (root / '.program-kit/managed.json').write_bytes(b'{}')
            plan = {'planDigest': 'fresh', 'conflicts': [], 'actions': [
                {'path': 'First.cs', 'kind': 'create', 'expectedHash': None},
                {'path': 'Second.cs', 'kind': 'create', 'expectedHash': None}]}
            with self.assertRaisesRegex(ValueError, 'inputs changed'):
                scaffold.apply(root, plan, {}, 'old')
            (root / 'Second.cs').write_bytes(b'consumer customization')
            with self.assertRaisesRegex(reconciliation.ReconciliationError, 'inputs changed'):
                scaffold.apply(root, plan, {'First.cs': b'new', 'Second.cs': b'new'}, 'fresh')
            self.assertFalse((root / 'First.cs').exists())
            self.assertEqual(b'consumer customization', (root / 'Second.cs').read_bytes())
            plan['conflicts'] = [{'path': 'Second.cs'}]
            with self.assertRaisesRegex(ValueError, 'consumer source preserved'):
                scaffold.apply(root, plan, {}, 'fresh')

    def test_interruption_rolls_back_all_created_source_and_preserves_state(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / '.program-kit').mkdir()
            (root / '.program-kit/managed.json').write_bytes(b'{"files":{}}')
            with patch.dict(os.environ, {'PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION': '1'}), self.assertRaises(OSError):
                reconciliation.apply_plan(root, [
                    {'kind': 'write', 'path': 'First.cs', 'content': b'one', 'expectedHash': None},
                    {'kind': 'write', 'path': 'Second.cs', 'content': b'two', 'expectedHash': None}], b'{"files":{}}')
            self.assertFalse((root / 'First.cs').exists())
            self.assertFalse((root / 'Second.cs').exists())
            self.assertEqual(b'{"files":{}}', (root / '.program-kit/managed.json').read_bytes())
            self.assertFalse(reconciliation.pending_transactions(root))

    def test_change_during_commit_preserves_authored_destination_and_rolls_back_earlier_write(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            (root / '.program-kit').mkdir()
            (root / '.program-kit/managed.json').write_bytes(b'{}')
            original = reconciliation.atomic_write
            def edit(path, data, suffix):
                original(path, data, suffix)
                if Path(path).name == 'First.cs':
                    (root / 'Second.cs').write_bytes(b'authored concurrently')
            with patch.object(reconciliation, 'atomic_write', side_effect=edit), self.assertRaisesRegex(reconciliation.ReconciliationError, 'preserved externally|preserved|Recovery preserved'):
                reconciliation.apply_plan(root, [
                    {'kind': 'write', 'path': 'First.cs', 'content': b'one'},
                    {'kind': 'write', 'path': 'Second.cs', 'content': b'two'}], b'{}')
            self.assertFalse((root / 'First.cs').exists())
            self.assertEqual(b'authored concurrently', (root / 'Second.cs').read_bytes())

    def test_aliased_parent_is_rejected(self):
        with FixtureDirectory() as directory:
            root = Path(directory)
            with patch.object(Path, 'is_symlink', return_value=True), self.assertRaisesRegex(ValueError, 'aliased'):
                scaffold.confined(root, 'src/File.cs')

    def test_transaction_diagnostic_names_recovery_without_private_payloads(self):
        result=scaffold.failure(reconciliation.ReconciliationError('PRIVATE_SOURCE_CANARY'))
        self.assertEqual('PKS303',result['code'])
        self.assertIn('.program-kit/transactions',result['repair'])
        self.assertNotIn('PRIVATE_SOURCE_CANARY',json.dumps(result))

    def test_exclusive_creation_preserves_an_intervening_authored_file(self):
        with FixtureDirectory() as directory:
            root=Path(directory);(root/'.program-kit').mkdir();(root/'.program-kit/managed.json').write_bytes(b'{}')
            original=Path.open
            def open_file(path, mode='r', *args, **kwargs):
                if path.name=='Second.cs' and mode=='xb':
                    with original(path,'wb') as stream:stream.write(b'authored after precheck')
                return original(path,mode,*args,**kwargs)
            with patch.object(Path,'open',open_file),self.assertRaisesRegex(reconciliation.ReconciliationError,'externally changed'):
                reconciliation.apply_plan(root,[{'kind':'create','path':'First.cs','content':b'one','expectedHash':None},
                    {'kind':'create','path':'Second.cs','content':b'two','expectedHash':None}],b'{}')
            self.assertFalse((root/'First.cs').exists())
            self.assertEqual(b'authored after precheck',(root/'Second.cs').read_bytes())


if __name__ == '__main__':
    unittest.main()
