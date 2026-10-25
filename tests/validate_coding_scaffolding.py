"""F4 independent ownership/creation/transaction negatives and source adapter tests."""
from pathlib import Path
import json
import os
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
                            'provider':['Orbyss.Foundation.PostgreSql']}.get(key, [])
                items = ''.join(f'<PackageReference Include="{name}" Version="0.3.7"/>' for name in packages)
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
            before = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            plan, outputs = scaffold.preview(root, root / 'specs/001-label', 'typed-label', self.owners)
            self.assertTrue(outputs and all(row['kind']=='create' for row in plan['actions']))
            self.assertFalse(plan['conflicts'])
            self.assertEqual(before, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root / 'docs/architecture').exists(), 'No consumer qualification/approval files are needed')
            api = root / self.owners['api']
            api.write_text(api.read_text().replace('Version="0.3.7"', 'Version="0.3.5"'))
            rejected = {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaisesRegex(ValueError, 'public problem contract'):
                scaffold.preview(root, root / 'specs/001-label', 'typed-label', self.owners)
            self.assertEqual(rejected, {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()})

    def test_emitted_csharp_readability_and_independent_syntax_negatives(self):
        from csharp_readability_check import check
        self.assertEqual(0, check())

    def setUp(self):
        self.owners = {k: f'src/{k}/{k}.csproj' for k in ('core', 'runtime', 'api', 'provider', 'test')}
        self.owners.update(frontend='web/app', generatedTypes='tools/openapi/labels/generated/types.ts')

    def test_exact_source_owner_split_and_generated_client_import(self):
        output = typed_operation.render(self.owners, ROOT / 'extensions')
        self.assertIn('src/core/ILabelOperations.cs', output)
        self.assertIn('src/runtime/LabelOperations.cs', output)
        self.assertIn('src/provider/PostgreSqlLabelStore.cs', output)
        api = output['src/api/LabelEndpoint.cs'].decode()
        self.assertIn('ILabelOperations operations', api)
        self.assertNotIn('ILabelStore', api)
        self.assertNotIn('store.WriteAsync', api)
        self.assertIn('RequestAborted', api)
        self.assertIn(b'../../../tools/openapi/labels/generated/types', output['web/app/src/client.ts'])
        self.assertFalse(any(p.endswith('.csproj') for p in output), 'no hidden project mutations')

    def test_submitted_commands_and_escaping_paths_are_not_adapters(self):
        for change in ({'command': 'anything'}, {'api': '../outside.csproj'}, {'runtime': self.owners['api']},
                       {'frontend': 'C:/private'}, {'generatedTypes': 'schema.json'}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'PKS300'):
                typed_operation.render({**self.owners, **change}, ROOT / 'extensions')

    def test_native_contracts_must_belong_to_the_actual_consuming_owner(self):
        api=[{'id':p,'version':'0.3.6'} for p in ('Orbyss.Foundation.Json.AspNetCore','Orbyss.Foundation.Web.ProblemDetails')]
        provider=[{'id':'Orbyss.Foundation.PostgreSql','version':'0.3.6'}]
        projects={self.owners['api']:{'packages':api},self.owners['provider']:{'packages':provider}}
        scaffold.native_contracts(projects,self.owners)
        with self.assertRaisesRegex(ValueError,'neighboring package'):
            scaffold.native_contracts({self.owners['api']:{'packages':[]},self.owners['provider']:{'packages':api+provider}},self.owners)
        for identity in ('Orbyss.Foundation.Json.AspNetCore','Orbyss.Foundation.Web.ProblemDetails'):
            old=[{**p,'version':'0.3.5'} if p['id']==identity else p for p in api]
            with self.assertRaises(ValueError):
                scaffold.native_contracts({self.owners['api']:{'packages':old},self.owners['provider']:{'packages':provider}},self.owners)

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
