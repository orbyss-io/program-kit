"""Pure typed-resource invariants and preservation at the legacy import boundary."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import composition_model as model


def example():
    value = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak-postgresql.json').read_text())
    return model.from_legacy(value)


class ResourceModel(unittest.TestCase):
    def test_root_eng_cannot_own_authored_source_but_nested_names_remain_valid(self):
        for path in ('tools/worker/Worker.csproj', 'tools/worker/eng/Worker.csproj'):
            graph = example(); graph['resources'][next(iter(model.resources(graph, 'feature')))]['path'] = path
            model.validate(graph)
        for path in ('eng/Worker.csproj', 'ENG/Worker.csproj'):
            graph = example(); graph['resources'][next(iter(model.resources(graph, 'feature')))]['path'] = path
            with self.assertRaisesRegex(ValueError, 'eng is disposable'):
                model.validate(graph)
        graph = example(); graph['resources']['application-shell']['source'] = 'eng/shells.json'
        with self.assertRaisesRegex(ValueError, 'eng is disposable'):
            model.validate(graph)

    def test_configuration_environment_requires_selected_ownership_and_product_destination(self):
        graph = example()
        feature = next(iter(model.resources(graph, 'feature')))
        binding = {'kind': 'configurationEnvironment', 'featureRef': feature, 'shellRef': 'application-shell',
                   'setting': 'Example:HmacSecret', 'environmentRef': 'PK_EXAMPLE_HMAC'}
        graph['bindings'].append(binding)
        model.validate(graph)
        resolved = model.configuration_environment_bindings(graph)[0]
        self.assertEqual('CShells__Shells__default__Configuration__Example__HmacSecret', resolved['environmentKey'])
        for setting in ('Foundation:Web:ClientSecret', 'foundation:PostgreSql:ConnectionString',
                        'Nuplane:Loading', 'Example:Bad__Key', 'Example', 'Example:../Secret'):
            with self.subTest(setting=setting):
                invalid = deepcopy(graph); invalid['bindings'][-1]['setting'] = setting
                with self.assertRaises(ValueError): model.validate(invalid)
        invalid = deepcopy(graph); invalid['bindings'][-1]['environmentRef'] = 'PK_SECRET;echo'
        with self.assertRaisesRegex(ValueError, 'explicit environment variable'): model.validate(invalid)
        invalid = deepcopy(graph); invalid['bindings'] = [row for row in invalid['bindings']
            if not (row['kind'] == 'featureShell' and row['featureRef'] == feature)]
        with self.assertRaisesRegex(ValueError, 'foreign feature/shell'): model.validate(invalid)
        graph['bindings'].append({**binding, 'setting': 'example:hmacsecret', 'environmentRef': 'PK_OTHER'})
        with self.assertRaisesRegex(ValueError, 'duplicate product configuration'): model.validate(graph)

    def test_configuration_environment_matches_exact_available_source_declaration(self):
        graph = example(); feature = next(iter(model.resources(graph, 'feature')))
        graph['bindings'].append({'kind': 'configurationEnvironment', 'featureRef': feature,
            'shellRef': 'application-shell', 'setting': 'Example:HmacSecret', 'environmentRef': 'PK_EXAMPLE_HMAC'})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual('native-declaration-not-present', model.provider_binding_declarations(root, graph)[0]['status'])
            path = root / Path(graph['resources'][feature]['path']).parent / 'settings.source.json'
            path.parent.mkdir(parents=True)
            declaration = {'schemaVersion': 2, 'packageId': graph['resources'][feature]['packageId'],
                'contracts': [{'complete': True, 'settings': [{'path': 'Example:Other'}]}]}
            path.write_text(json.dumps(declaration))
            with self.assertRaisesRegex(ValueError, 'does not cover composition binding'):
                model.provider_binding_declarations(root, graph)
            declaration['contracts'][0]['settings'][0]['path'] = 'example:hmacsecret'
            path.write_text(json.dumps(declaration))
            self.assertIn('native-activation-required', model.provider_binding_declarations(root, graph)[0]['status'])
            declaration['packageId'] = 'Foreign.Package'; path.write_text(json.dumps(declaration))
            with self.assertRaisesRegex(ValueError, 'unsupported native provider settings declaration'):
                model.provider_binding_declarations(root, graph)

    def test_declared_external_inputs_detect_add_change_remove_and_reject_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); folder = root / 'docs/brand'; folder.mkdir(parents=True)
            path = folder / 'logo.png'; path.write_bytes(b'synthetic-source')
            resource = {'inputs': ['docs/brand']}
            before = model.resource_input_files(root, resource)
            path.write_bytes(b'changed-source')
            self.assertNotEqual(before, model.resource_input_files(root, resource))
            second = folder / 'theme.css'; second.write_bytes(b'body {}')
            added = model.resource_input_files(root, resource)
            self.assertIn('docs/brand/theme.css', added)
            path.unlink()
            self.assertNotIn('docs/brand/logo.png', model.resource_input_files(root, resource))
            with self.assertRaisesRegex(ValueError, 'missing'):
                model.resource_input_files(root, {'inputs': ['docs/brand/logo.png']})
            self.assertEqual({}, model.resource_input_files(root, {'inputs': ['docs/brand/logo.png']}, required=False))
            for invalid in ('../outside', 'C:/outside', 'docs\\brand', 'artifacts/private'):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    model.resource_input_files(root, {'inputs': [invalid]})

    def test_declared_external_inputs_reject_actual_link_or_junction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); target = root / 'brand'; target.mkdir()
            (target / 'logo.png').write_bytes(b'synthetic-logo')
            link = root / 'linked-brand'
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                if os.name != 'nt':
                    raise
                created = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(0, created.returncode, 'The host could create neither a test symlink nor an owned junction')
                self.assertTrue(link.is_junction())
            with self.assertRaisesRegex(ValueError, 'linked declared'):
                model.resource_input_files(root, {'inputs': ['linked-brand']})

    def test_shell_path_base_rejects_aliases_traversal_and_nonlocal_values(self):
        for prefix in ('/', '/a/', '//a', '/../a', '/a//b', '/a%2fb', '/a?b', '/a#b', '/a\\b', True, 7):
            with self.subTest(prefix=prefix):
                graph = example(); graph['resources']['application-shell']['pathBase'] = prefix
                with self.assertRaisesRegex(ValueError, 'shell.pathBase'): model.validate(graph)
        for prefix in ('', '/products/orders'):
            graph = example(); graph['resources']['application-shell']['pathBase'] = prefix
            model.validate(graph); self.assertEqual(prefix, model.shell_path_base(graph, 'application-shell'))

    def test_nested_shell_projects_native_profile_callbacks_and_rejects_overlay_drift(self):
        import composition_render as renderer
        graph = example(); graph['resources']['application-shell']['pathBase'] = '/products/orders'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            profile = json.loads(files['config/program-kit/web-profile.shells.json'][0])
            shell = graph['resources']['application-shell']['name']
            configuration = profile['CShells']['Shells'][shell]['Configuration']
            self.assertEqual('products/orders', configuration['WebRouting']['Path'])
            contract = json.loads(files['config/program-kit/foundation-settings.contract.json'][0])
            renderer.validate_consumer_configuration(graph, 'application-shell', contract['shells']['application-shell'],
                configuration, contract['environment'])
            configuration['WebRouting']['Path'] = 'unreviewed'
            with self.assertRaisesRegex(ValueError, 'canonical WebRouting:Path'):
                renderer.validate_consumer_configuration(graph, 'application-shell', contract['shells']['application-shell'],
                    configuration, contract['environment'])
            auth = renderer.auth_binding(graph, 'application-shell')
            client_id = model.environment(graph)[auth['clientRef']]['clientId']
            realm = json.loads(next(data[0] for name, data in files.items() if name.startswith('deploy/keycloak/') and name.endswith('-realm.json')))
            client = next(row for row in realm['clients'] if row['clientId'] == client_id)
            self.assertTrue(client['redirectUris'][0].endswith('/products/orders/signin-oidc'))
            self.assertTrue(client['attributes']['post.logout.redirect.uris'].endswith('/products/orders/signout-callback-oidc'))
            web = json.loads(files['eng/web/compositions/application-shell.json'][0])
            self.assertTrue(all(row['path'].startswith('/products/orders/') for row in web['routes'].values()))

    def test_private_provider_binding_projects_exact_key_and_discloses_static_limit(self):
        graph = example()
        shell = next(iter(model.resources(graph, 'shell')))
        host = next(iter(model.resources(graph, 'host')))
        feature = next(row['featureRef'] for row in model.bindings(graph, 'databaseProvider'))
        graph['resources']['owned-files'] = {'kind':'privateFiles','ownerRef':'fixture-owner'}
        graph['authority'] = {'architectureMap':'docs/architecture/fixture.json','decisionIds':['fixture']}
        graph['bindings'].append({'kind':'privateFiles','filesRef':'owned-files','hostRef':host,
                                  'shellRef':shell,'featureRef':feature,'setting':'Root'})
        for configured in graph['environments'].values():
            configured['resources']['owned-files']={'directory':'artifacts/private/owned-files'}
        model.validate(graph)
        binding = model.private_file_bindings(graph)[0]
        self.assertEqual('EvidenceFiles:Root', binding['configurationKey'])
        self.assertTrue(binding['environmentKey'].endswith('__Configuration__EvidenceFiles__Root'))
        self.assertEqual('/private-evidence/owned-files', binding['runtimePath'])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual('native-declaration-not-present', model.provider_binding_declarations(root,graph)[0]['status'])
            metadata = root/Path(binding['featurePath']).parent/'settings.source.json'
            metadata.parent.mkdir(parents=True)
            declaration = {'schemaVersion':2,'packageId':graph['resources'][feature]['packageId'],
                           'contracts':[{'complete':True,'settings':[{'path':'PolicyEvidence:RootPath'}]}]}
            metadata.write_text(json.dumps(declaration))
            with self.assertRaisesRegex(ValueError,'does not cover composition binding'):
                model.provider_binding_declarations(root,graph)
            declaration['contracts'][0]['settings'][0]['path']='evidencefiles:ROOT'
            metadata.write_text(json.dumps(declaration))
            self.assertIn('native-activation-required',model.provider_binding_declarations(root,graph)[0]['status'])

    def ordinary_provider_graph(self, database=True, declared=True):
        graph = example()
        if not database:
            removed = {name for name, row in graph['resources'].items() if row['kind'] in {'database', 'databaseServer'}
                       or row['kind'] == 'feature' and row['role'] == 'provider'}
            graph['resources'] = {name: row for name, row in graph['resources'].items() if name not in removed}
            graph['bindings'] = [row for row in graph['bindings'] if not (set(row.values()) & removed)]
            for env in graph['environments'].values():
                for name in removed:
                    env['resources'].pop(name, None)
        graph['resources']['files-provider'] = {'kind': 'feature', 'path': 'src/Evidence.Files/Evidence.Files.csproj',
            'packageId': 'Evidence.Files', 'featureIdentity': 'Existing.FilesIdentity', 'role': 'provider'}
        if declared:
            graph['resources']['files-provider']['responsibility'] = 'runtime'
        graph['bindings'].append({'kind': 'featureShell', 'featureRef': 'files-provider', 'shellRef': 'application-shell'})
        return graph

    def test_non_database_provider_uses_native_shell_feature_without_foreign_dependencies(self):
        import composition_render as renderer
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as temporary:
            files = renderer.materialize(Path(temporary), self.ordinary_provider_graph(database=False),
                                         ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
        source = files['src/Evidence.Files/ProviderFeature.cs'][0].decode()
        self.assertIn('ProviderFeature : IShellFeature', source)
        self.assertIn('ShellFeature("Existing.FilesIdentity")', source)
        self.assertNotIn('Prepare', source); self.assertNotIn('DbContext', source); self.assertNotIn('MapEndpoints', source)
        project = ET.fromstring(files['src/Evidence.Files/Evidence.Files.csproj'][0])
        self.assertEqual({'CShells.Abstractions'}, {row.get('Include') for row in project.iter('PackageReference')})
        self.assertFalse(list(project.iter('FrameworkReference')))
        self.assertFalse(any(name.endswith('Prepare.cs') for name in files))
        contract = json.loads(files['config/program-kit/foundation-settings.contract.json'][0])
        self.assertNotIn('Orbyss.Foundation.PostgreSql', contract['packages'])

    def test_mixed_database_and_ordinary_provider_select_only_actual_capabilities(self):
        import composition_render as renderer
        import xml.etree.ElementTree as ET
        graph = self.ordinary_provider_graph()
        graph['resources']['files-provider']['capabilityPackages'] = ['Orbyss.Foundation.Execution']
        with tempfile.TemporaryDirectory() as temporary:
            files = renderer.materialize(Path(temporary), graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
        provider = files['src/Evidence.Files/ProviderFeature.cs'][0].decode()
        self.assertIn('DependsOn = ["Orbyss.Foundation.Execution"]', provider)
        self.assertNotIn('PostgreSql', provider)
        self.assertEqual({'CShells.Abstractions', 'Orbyss.Foundation.Execution'},
                         {row.get('Include') for row in ET.fromstring(files['src/Evidence.Files/Evidence.Files.csproj'][0]).iter('PackageReference')})
        database_project = next(row['path'] for name, row in graph['resources'].items()
                                if row['kind'] == 'feature' and row['role'] == 'provider' and name != 'files-provider')
        self.assertIn('AddFoundationPostgreSql', files[(Path(database_project).parent / 'ProviderFeature.cs').as_posix()][0].decode())
        ownership = json.loads(files['config/program-kit/architecture.json'][0])['runtimeComposition']['projects']
        self.assertEqual(['owned runtime capability registration'], next(row for row in ownership if row['path'] ==
                         'src/Evidence.Files/Evidence.Files.csproj')['responsibilities'][0]['effects'])

    def test_reviewed_runtime_provider_is_not_coerced_to_persistence(self):
        graph = self.ordinary_provider_graph(declared=False)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [{
                'path': 'src/Evidence.Files/Evidence.Files.csproj', 'role': 'provider',
                'responsibilities': [{'name': 'Owned files adapter', 'kind': 'runtime', 'effects': ['owned file access']}]}]}}))
            self.assertEqual('runtime', model.project_definition(graph['resources']['files-provider'], root)['responsibility'])

    def test_database_binding_cannot_silently_convert_runtime_provider(self):
        graph = self.ordinary_provider_graph()
        graph['bindings'].append(dict(next(row for row in graph['bindings'] if row['kind'] == 'databaseProvider'),
                                      featureRef='files-provider', context='FilesContext', policy='files'))
        with self.assertRaisesRegex(ValueError, 'runtime-only'):
            model.validate(graph)

    def test_mixed_runtime_and_http_follow_source_responsibilities_and_preserve_identities(self):
        import composition_render as renderer
        import xml.etree.ElementTree as ET
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example()
            runtime = {'kind': 'feature', 'path': 'src/PolicyPortfolio/PolicyPortfolio.csproj',
                       'packageId': 'PolicyPortfolio', 'featureIdentity': 'Existing.PolicyIdentity',
                       'role': 'implementation', 'capabilityPackages': ['Orbyss.Foundation.Execution']}
            graph['resources']['policy-runtime'] = runtime
            graph['bindings'].append({'kind': 'featureShell', 'featureRef': 'policy-runtime', 'shellRef': 'application-shell'})
            (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            owned = {'path': runtime['path'], 'role': 'implementation', 'projectReferences': [],
                     'packageReferences': ['CShells.Abstractions', 'Orbyss.Foundation.Execution'],
                     'responsibilities': [{'name': 'PolicyPortfolio.Lifecycle', 'kind': 'runtime',
                                           'effects': ['owned policy effects']}]}
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [owned]}}))
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            source = files['src/PolicyPortfolio/PolicyPortfolioFeature.cs'][0].decode()
            self.assertIn('PolicyPortfolioFeature : IShellFeature', source)
            self.assertIn('ShellFeature("Existing.PolicyIdentity", DependsOn = ["Orbyss.Foundation.Execution"])', source)
            self.assertNotIn('IWebShellFeature', source); self.assertNotIn('MapEndpoints', source)
            project = ET.fromstring(files[runtime['path']][0])
            self.assertEqual(project.findtext('./PropertyGroup/FoundationFeatureIdentity'), runtime['featureIdentity'])
            self.assertEqual(project.findtext('./PropertyGroup/FoundationComposeForOpenApi'), 'false')
            references = {row.get('Include') for row in project.iter('PackageReference')}
            self.assertEqual(references, {'CShells.Abstractions', 'Orbyss.Foundation.Execution'})
            self.assertFalse(list(project.iter('FrameworkReference')))
            api = files['src/Application.Api/ApiFeature.cs'][0].decode()
            self.assertIn('ApiFeature : IWebShellFeature', api)
            api_refs = {row.get('Include') for row in ET.fromstring(files['src/Application.Api/Application.Api.csproj'][0]).iter('PackageReference')}
            self.assertNotIn('Orbyss.Foundation.Authentication.BffCookie', api_refs)
            self.assertNotIn('Orbyss.Foundation.Web.HostedPages', api_refs)
            generated = json.loads(files['config/program-kit/architecture.json'][0])['runtimeComposition']['projects']
            self.assertEqual(next(row for row in generated if row['path'] == runtime['path'])['responsibilities'], owned['responsibilities'])
            activations = json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']['default']['Features']
            self.assertIn(runtime['featureIdentity'], activations)
            obsolete = root / 'src/PolicyPortfolio/ApiFeature.cs'
            obsolete.parent.mkdir(parents=True)
            previous = b'[ShellFeature("Existing.PolicyIdentity")] public sealed class ApiFeature : IWebShellFeature { /* owned registration */ }'
            obsolete.write_bytes(previous)
            with self.assertRaisesRegex(ValueError, 'retained customized API seam'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            self.assertEqual(obsolete.read_bytes(), previous)
            obsolete.write_bytes(previous.replace(b'IWebShellFeature', b'IShellFeature'))
            retained = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            self.assertNotIn('src/PolicyPortfolio/PolicyPortfolioFeature.cs', retained)
            self.assertEqual(obsolete.read_bytes(), previous.replace(b'IWebShellFeature', b'IShellFeature'))
            obsolete.write_bytes(previous)
            state = root / 'config/program-kit/managed.json'; state.parent.mkdir(parents=True, exist_ok=True)
            import hashlib
            state.write_text(json.dumps({'files': {'src/PolicyPortfolio/ApiFeature.cs': {
                'ownership': 'scaffold', 'contribution': 'foundation',
                'sourceIdentity': '../../scripts/foundation_composition.py',
                'baselineHash': hashlib.sha256(previous).hexdigest()}}}))
            renderer.admit_runtime_reconciliation(root, model.project_definition(runtime, root))
            state.unlink(); obsolete.unlink()
            runtime['capabilityPackages'] = ['Orbyss.Foundation.Unselected']
            with self.assertRaisesRegex(ValueError, 'selected profile is missing package knowledge'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            runtime['capabilityPackages'] = ['Orbyss.Foundation.Execution']
            runtime['responsibility'] = 'http'
            with self.assertRaisesRegex(ValueError, 'conflicts with source authority'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')

    def test_feature_capability_packages_use_exact_selected_profile_and_remain_optional(self):
        import composition_render as renderer
        from dependency_profile import resolver
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); graph = example()
            feature = graph['resources']['feature-0']
            feature['capabilityPackages'] = ['Orbyss.Foundation.Tasks', 'Orbyss.Foundation.Tasks.Abstractions']
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            contract = json.loads(files[renderer.CONTRACT][0])['shells']['application-shell']
            catalog = resolver().effective_dependency_context(root)['catalog']
            selected_version = catalog['packages']['nuget:Orbyss.Foundation.Tasks']['version']
            self.assertEqual(selected_version, contract['packages']['Orbyss.Foundation.Tasks'])
            references = {row.get('Include') for row in ET.fromstring(files[feature['path']][0]).iter('PackageReference')}
            self.assertIn('Orbyss.Foundation.Tasks', references)
            self.assertIn('Orbyss.Foundation.Tasks.Abstractions', references)
            feature['capabilityPackages'] = []
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            self.assertNotIn('Orbyss.Foundation.Tasks', json.loads(files[renderer.CONTRACT][0])['packages'])
            feature['capabilityPackages'] = ['Orbyss.Foundation.ArbitraryPrefixMatch']
            with self.assertRaisesRegex(ValueError, 'selected profile is missing package knowledge'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')

    def test_authored_identity_seams_preserve_filenames_projects_and_provider_helpers(self):
        import composition_render as renderer
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); graph = example()
            runtime = {'kind': 'feature', 'path': 'src/Owned.Runtime/Owned.Runtime.csproj',
                       'packageId': 'Owned.Runtime', 'featureIdentity': 'Owned.Runtime.Feature',
                       'role': 'implementation', 'responsibility': 'runtime'}
            graph['resources']['owned-runtime'] = runtime
            graph['bindings'].append({'kind': 'featureShell', 'featureRef': 'owned-runtime', 'shellRef': 'application-shell'})
            authored = {}
            for index, feature in enumerate(model.resources(graph, 'feature').values()):
                folder = root / Path(feature['path']).parent; folder.mkdir(parents=True)
                path = folder / ('AuthoredRegistration' + str(index) + '.cs')
                interface = 'IWebShellFeature' if model.project_definition(feature)['responsibility'] == 'http' else 'IShellFeature'
                path.write_text('[ShellFeature("' + feature['featureIdentity'] + '")] public sealed class Owned : ' + interface + ' {}')
                project = root / feature['path']; project.write_text('<Project><ItemGroup><PackageReference Include="Consumer.Owned" /></ItemGroup></Project>')
                authored[path] = path.read_bytes(); authored[project] = project.read_bytes()
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            for path, content in authored.items():
                self.assertEqual(content, path.read_bytes())
                self.assertNotIn(path.relative_to(root).as_posix(), files)
            self.assertFalse(any(path.endswith('.cs') for path in files))
            duplicate = root / 'src/Owned.Runtime/UnexpectedName.cs'
            duplicate.write_text('[ShellFeature("Owned.Runtime.Feature")] public sealed class Duplicate : IShellFeature {}')
            with self.assertRaisesRegex(ValueError, 'duplicate ShellFeature identity'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            duplicate.write_text('// [ShellFeature("Owned.Runtime.Feature")] commented declaration\n')
            renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')

    def test_unknown_authored_feature_declarations_require_reconciliation_without_generating_duplicates(self):
        import composition_render as renderer
        project = {'path': 'src/Runtime/Runtime.csproj', 'featureIdentity': 'Owned.Runtime', 'responsibility': 'runtime'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); folder = root / 'src/Runtime'; folder.mkdir(parents=True)
            path = folder / 'Registration.cs'
            for source in ('[ShellFeature(FeatureNames.Runtime)] class Owned : IShellFeature {}',
                           'using Registration = CShells.Features.ShellFeatureAttribute; [Registration("Owned.Runtime")] class Owned {}',
                           '#if OPTIONAL\n[ShellFeature("Owned.Runtime")] class Owned {}\n#endif'):
                path.write_text(source)
                with self.assertRaisesRegex(ValueError, 'authored source reconciliation'):
                    renderer.authored_feature_owner(root, project)
                self.assertEqual(source, path.read_text())
            path.write_text('const string Example = """[ShellFeature("Owned.Runtime")]""";')
            self.assertIsNone(renderer.authored_feature_owner(root, project))
            path.write_text('[Other, CShells.Features.ShellFeature("Owned.Runtime")] class Owned : IShellFeature {}')
            self.assertEqual('src/Runtime/Registration.cs', renderer.authored_feature_owner(root, project))
            path.write_text('using Features = CShells.Features; [Features.ShellFeature("Owned.Runtime")] class Owned : IShellFeature {}')
            self.assertEqual('src/Runtime/Registration.cs', renderer.authored_feature_owner(root, project))

    def test_customized_selected_scaffolds_keep_prior_ownership_until_actual_retirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True); graph = example()
            (root / model.INPUT).parent.mkdir(parents=True, exist_ok=True)
            (root / model.INPUT).write_text(json.dumps(graph))
            command = [sys.executable, '-B', str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                       '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
            def synchronize(extra=()):
                result = subprocess.run([*command, *extra], capture_output=True, text=True, timeout=90)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            synchronize()
            feature = next(row for row in model.resources(graph, 'feature').values() if row['role'] == 'implementation')
            project = feature['path']; source = (Path(project).parent / 'ApiFeature.cs').as_posix()
            state_path = root / 'config/program-kit/managed.json'
            before = json.loads(state_path.read_text())
            retained = {}
            for relative in (project, source):
                path = root / relative
                path.write_bytes(path.read_bytes() + (b'\n<!-- synthetic authored project -->\n'
                                 if relative == project else b'\n// synthetic authored registration\n'))
                retained[relative] = path.read_bytes()
            synchronize()
            after = json.loads(state_path.read_text())
            for relative, content in retained.items():
                self.assertEqual(content, (root / relative).read_bytes())
                self.assertIn(relative, after['files'], 'Still-selected authored scaffold was prematurely retired')
                self.assertEqual(before['files'][relative], after['files'][relative], 'Preservation must not authenticate authored bytes')
            synchronize(['--check'])

    def test_composition_only_reconciliation_preserves_unrelated_conflicts_and_rolls_back(self):
        import subprocess
        import os
        import hashlib
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example(); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            input_path = root / model.INPUT; input_path.write_text(json.dumps(graph))
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                       '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
            def run(extra=(), expected=0, env=None):
                observed = subprocess.run([*command, *extra], cwd=ROOT, capture_output=True, text=True,
                                          encoding='utf-8', timeout=90, env=env)
                self.assertEqual(expected, observed.returncode, observed.stdout + observed.stderr)
                return json.loads(observed.stdout.split('committed reconciliation transaction:')[0])
            run()
            architecture_path = root / 'config/program-kit/architecture.json'
            architecture = json.loads(architecture_path.read_text())
            architecture['runtimeComposition']['projects'][0]['responsibilities'][0]['effects'].append('authored boundary')
            architecture_path.write_text(json.dumps(architecture))
            shell_path = root / 'shells.json'; shell = json.loads(shell_path.read_text())
            shell['CShells']['Shells']['default']['Configuration'] = {'ConsumerOwned': {'policy': 'keep'}}
            shell_path.write_text(json.dumps(shell))
            helper = root / 'scripts/openapi_contracts.py'; helper.write_bytes(helper.read_bytes() + b'\n# authored local repair\n')
            central = root / 'Directory.Packages.props'
            import re
            central.write_text(re.sub(r'  <Import Project="config/program-kit/build/ProgramKit.Foundation.props"\s+Condition="[^"]+"\s*/>', '', central.read_text())
                               .replace('</Project>', '<ItemGroup><PackageVersion Include="Consumer.Exact" Version="1.2.3" /></ItemGroup></Project>'))
            central_before = central.read_text()
            retired = root / '.dockerignore'; retired.write_text('authored retired file\n')
            state_path = root / 'config/program-kit/managed.json'; state = json.loads(state_path.read_text())
            state['files']['.dockerignore'] = {'ownership': 'managed', 'contribution': 'base',
                                              'baselineHash': hashlib.sha256(b'old baseline').hexdigest(),
                                              'lastWrittenHash': hashlib.sha256(b'old baseline').hexdigest()}
            # Fictional prior-release helper bytes, honestly recorded as that
            # installation's baseline; the scoped native transaction must update
            # these dependencies as well as its direct runner.
            for relative in ('scripts/runtime_closure.py', 'scripts/prepare_hosted_pages.py'):
                old_helper = root / relative
                old_helper.write_text('# synthetic prior release helper\n')
                digest = hashlib.sha256(old_helper.read_bytes()).hexdigest()
                state['files'][relative].update(baselineHash=digest, templateHash=digest,
                                               lastWrittenHash=digest, installedHash=digest)
            state_path.write_text(json.dumps(state))
            for feature in model.resources(graph, 'feature').values():
                folder = root / Path(feature['path']).parent
                generated = folder / ('ProviderFeature.cs' if feature['role'] == 'provider' else 'ApiFeature.cs')
                generated.rename(folder / 'AuthoredRegistration.cs')
            graph['resources']['application-shell']['settings']['RemoteAuthenticationTimeoutSeconds'] = 120
            input_path.write_text(json.dumps(graph))
            protected = {p: p.read_bytes() for p in [architecture_path, shell_path, helper, retired,
                         *root.glob('src/**/*.cs'), *root.glob('src/**/*.csproj')]}
            baseline = json.loads(state_path.read_text())
            whole = run(['--check'], expected=2)
            self.assertIn('scripts/openapi_contracts.py', {row['path'] for row in whole['conflicts']})
            self.assertIn('.dockerignore', {row['path'] for row in whole['conflicts']})
            preview = run(['--composition-only', '--check'], expected=1)
            self.assertEqual('composition-configuration', preview['scope'])
            self.assertFalse(preview['conflicts'])
            self.assertFalse(any(row['path'] in {p.relative_to(root).as_posix() for p in protected} for row in preview['actions']))
            self.assertEqual(baseline, json.loads(state_path.read_text()))
            def snapshot():
                return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()
                        and '.program-kit/transactions/' not in p.relative_to(root).as_posix()}
            before = snapshot()
            failure_env = dict(os.environ, PROGRAMKIT_TEST_SYNC_FAIL_AFTER_ACTION='2')
            run(['--composition-only'], expected=2, env=failure_env)
            self.assertEqual(before, snapshot())
            run(['--composition-only', '--plan-digest', preview['planDigest']])
            for relative in ('scripts/runtime_closure.py', 'scripts/prepare_hosted_pages.py'):
                self.assertEqual((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files' / relative).read_bytes(),
                                 (root / relative).read_bytes())
            # Launch against only the installed engineering helpers. Source-tree
            # imports cannot accidentally satisfy the freshness assertion.
            installed_probe = r'''
import json, sys
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root / 'scripts'))
import prepare_hosted_pages as frontend
import runtime_closure
assert Path(frontend.__file__).parent == root / 'scripts'
assert Path(runtime_closure.__file__).parent == root / 'scripts'
directory = root / 'src/SyntheticWeb'; directory.mkdir(parents=True, exist_ok=True)
(directory / 'index.tsx').write_text('export {}')
brand = root / 'docs/synthetic-brand.css'; brand.parent.mkdir(parents=True, exist_ok=True); brand.write_text('body {}')
graph = {'resources': {'synthetic-web': {'directory': 'src/SyntheticWeb', 'inputs': ['docs/synthetic-brand.css']}}}
before = frontend.input_snapshot(root, graph, 'synthetic-web')
brand.write_text('body { color: blue; }')
assert before != frontend.input_snapshot(root, graph, 'synthetic-web')
brand.unlink()
try:
    frontend.input_snapshot(root, graph, 'synthetic-web')
except ValueError as error:
    assert 'declared source input is missing' in str(error)
else:
    raise AssertionError('Removed external input silently accepted')
'''
            installed = subprocess.run([sys.executable, '-I', '-B', '-c', installed_probe, str(root)],
                                       cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            import xml.etree.ElementTree as ET
            self.assertIn('Include="Consumer.Exact" Version="1.2.3"', central.read_text())
            self.assertTrue(any(row.get('Project') == 'config/program-kit/build/ProgramKit.Foundation.props' for row in ET.parse(central).findall('Import')))
            self.assertEqual(central_before, central.read_text().replace(
                '  <Import Project="config/program-kit/build/ProgramKit.Foundation.props" Condition="Exists(\'config/program-kit/build/ProgramKit.Foundation.props\')" />\n', ''))
            after = json.loads(state_path.read_text())
            for path in protected:
                relative = path.relative_to(root).as_posix()
                self.assertEqual(protected[path], path.read_bytes())
                if relative in baseline['files']:
                    self.assertEqual(baseline['files'][relative], after['files'][relative])
            run(['--composition-only', '--check'])
            managed_profile = root / 'config/program-kit/web-profile.shells.json'
            managed_profile.write_bytes(managed_profile.read_bytes() + b'\n')
            conflict = run(['--composition-only', '--check'], expected=2)
            self.assertIn('config/program-kit/web-profile.shells.json', {row['path'] for row in conflict['conflicts']})

    def test_missing_active_composition_is_an_advisory_for_bff_compatibility_scaffold(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(root), '--profile-selected', '--web-profile', 'bff-cookie', '--check']
            result = subprocess.run([*command, '--json'], capture_output=True, text=True, timeout=60)
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            advisory = json.loads(result.stdout)['advisories'][0]
            self.assertEqual('PKF101', advisory['id'])
            self.assertIn('--composition-only --check --json', advisory['message'])
            human = subprocess.run(command, capture_output=True, text=True, timeout=60)
            self.assertEqual(1, human.returncode, human.stdout + human.stderr)
            self.assertIn('advisory PKF101:', human.stdout)
            alternative = subprocess.run([*command[:command.index('bff-cookie')], 'none', '--check', '--json'],
                                         capture_output=True, text=True, timeout=60)
            self.assertEqual(1, alternative.returncode, alternative.stdout + alternative.stderr)
            self.assertNotIn('advisories', json.loads(alternative.stdout))
            self.assertEqual([], list(root.rglob('*')), 'Preview/advisory must not mutate the target or start an application')

    def test_missing_responsibility_does_not_guess_from_api_filename(self):
        feature = {'path': 'src/Guessed.Api/Guessed.Api.csproj', 'packageId': 'Guessed.Api',
                   'featureIdentity': 'Unchanged', 'role': 'implementation'}
        with self.assertRaisesRegex(ValueError, 'declare runtime or HTTP'):
            model.project_definition(feature)
        feature['responsibility'] = 'runtime'
        self.assertEqual(model.project_definition(feature)['responsibility'], 'runtime')

    def test_typed_interactive_window_preserves_override_and_short_network_budget(self):
        import composition_render as renderer
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example()
            def web():
                files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
                return json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']['default']['Configuration']['Foundation']['Web']
            defaults = web()
            self.assertEqual(defaults['RemoteAuthenticationTimeoutSeconds'], 900)
            self.assertEqual(defaults['DiscoveryTimeoutSeconds'], 3)
            graph['resources']['application-shell']['settings'].update(RemoteAuthenticationTimeoutSeconds=120, DiscoveryTimeoutSeconds=4)
            overridden = web()
            self.assertEqual(overridden['RemoteAuthenticationTimeoutSeconds'], 120)
            self.assertEqual(overridden['DiscoveryTimeoutSeconds'], 4)

    def test_activation_package_owners_come_from_drift_checked_capture(self):
        import composition_render as renderer
        import shutil
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
        import release_bundle
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example()
            graph['resources']['page'] = {'kind': 'frontend', 'directory': 'web/page', 'entry': 'src/app.ts'}
            graph['bindings'].append({'kind': 'frontend', 'frontendRef': 'page', 'shellRef': 'application-shell', 'routeId': 'page', 'path': '/'})
            shutil.copytree(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts', root / 'scripts')
            shutil.copytree(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/tools', root / 'tools')
            (root / model.INPUT).parent.mkdir(parents=True, exist_ok=True)
            (root / model.INPUT).write_text(json.dumps(graph))
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            for path, (payload, _) in files.items():
                target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
            identity = 'Orbyss.Foundation.Web.HostedPages'
            self.assertNotIn(identity, release_bundle.BUILT_IN_FEATURE_PACKAGES)
            owners = release_bundle.typed_publisher_features(root, {identity})
            import dependency_profile
            selected = dependency_profile.resolver().effective_dependency_context(root)
            version = selected['catalog']['packages']['nuget:Orbyss.Foundation.Web.HostedPages']['version']
            self.assertEqual(owners, {identity: ('Orbyss.Foundation.Web.HostedPages', version)})
            self.assertEqual(release_bundle.typed_publisher_features(root, {'Unselected.Consumer'}), {})
            profile = root / 'config/program-kit/web-profile.shells.json'; profile.write_bytes(profile.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'managed composition output changed'):
                release_bundle.typed_publisher_features(root, {identity})

    def test_native_sync_reconciles_untouched_runtime_scaffold_and_preserves_custom_project(self):
        import subprocess
        import xml.etree.ElementTree as ET
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example(); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            input_path = root / model.INPUT; input_path.write_text(json.dumps(graph))
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                       '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
            def sync():
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            sync()
            pins = {path: (root / path).read_bytes() for path in ('config/program-kit/build/ProgramKit.Foundation.props', 'config/program-kit/build/ProgramKit.Packages.props')}
            project = graph['resources']['feature-0']
            project['capabilityPackages'] = ['Orbyss.Foundation.Execution']
            input_path.write_text(json.dumps(graph)); sync()
            self.assertIn('Orbyss.Foundation.Execution', (root / Path(project['path']).parent / 'ApiFeature.cs').read_text())
            project['capabilityPackages'] = []; project['responsibility'] = 'runtime'
            input_path.write_text(json.dumps(graph))
            architecture_path = root / 'config/program-kit/architecture.json'
            architecture = json.loads(architecture_path.read_text())
            for owner in architecture['runtimeComposition']['projects']:
                if owner['path'] == project['path']:
                    owner['responsibilities'][0]['kind'] = 'runtime'
            architecture_path.write_text(json.dumps(architecture))
            sync()
            folder = root / Path(project['path']).parent
            self.assertFalse((folder / 'ApiFeature.cs').exists())
            # The explicit runtime responsibility wins even with an .Api path.
            self.assertIn('ApplicationApiFeature : IShellFeature', (folder / 'ApplicationApiFeature.cs').read_text())
            runtime_project = root / project['path']
            document = ET.fromstring(runtime_project.read_bytes())
            self.assertEqual({row.get('Include') for row in document.iter('PackageReference')}, {'CShells.Abstractions'})
            self.assertEqual(document.findtext('./PropertyGroup/FoundationFeatureIdentity'), project['featureIdentity'])
            for path, original in pins.items(): self.assertEqual((root / path).read_bytes(), original)
            custom = runtime_project.read_bytes().replace(b'</Project>', b'<!-- owned customization --></Project>')
            runtime_project.write_bytes(custom)
            sync(); self.assertEqual(runtime_project.read_bytes(), custom)

    def test_accepted_selection_keeps_native_pins_and_activation_with_its_owner(self):
        from composition_fixture import two_apps, accept_fixture
        import composition_render as renderer
        import xml.etree.ElementTree as ET
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = two_apps(ROOT)
            accept_fixture(root, graph, ROOT)
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            admitted = renderer.accepted_selection(root)
            native = {row['packageId'] for output in admitted['managedOutputs']
                      if output['kind'] == 'nuget-central-pins' for row in output['entries']}
            generated = {row.get('Include') for row in ET.fromstring(files['config/program-kit/build/ProgramKit.Foundation.props'][0]).iter('PackageVersion')}
            self.assertTrue(native)
            self.assertFalse(native & generated)
            self.assertNotIn('config/program-kit/build/ProgramKit.BuildingBlocks.props', files)
            contracts = json.loads(files[renderer.CONTRACT][0])['shells']
            self.assertIn('Orbyss.Foundation.DomainEvents', contracts['application-shell']['packages'])
            self.assertNotIn('Orbyss.Foundation.DomainEvents', contracts['assessment-shell']['packages'])
            for feature in model.resources(graph, 'feature').values():
                references = {row.get('Include') for row in ET.fromstring(files[feature['path']][0]).iter('PackageReference')}
                self.assertNotIn('Orbyss.Foundation.DomainEvents', references)

    def test_import_preserves_assigned_ids_and_callbacks(self):
        value = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak-postgresql.json').read_text())
        value['application']['callbackPath'] = '/custom-signin'
        value['identity']['administrationOrigin'] = 'http://identity-admin:8080'
        value['identity']['backchannelOrigin'] = 'http://identity-metadata:8080'
        converted = model.from_legacy(value)
        projected = model.legacy_view(converted, 'application-shell')
        for key in ('application', 'identity', 'runtime', 'projects'):
            self.assertEqual(value[key], projected[key])
        self.assertEqual(converted['schemaVersion'], 2)
        self.assertNotIn('identity', converted)

    def test_legacy_migration_preserves_identity_branding_and_archive(self):
        import composition_migrate as migration
        value = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak.json').read_text())
        value['theme']['branding'] = {'displayName': 'Harbor Workspace', 'accentColor': '#0088aa'}
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            original = json.dumps(value).encode()
            (root / model.INPUT).write_bytes(original)
            plan = migration.preview(root)
            migration.apply(root, plan['planDigest'])
            converted = model.load(root)
            self.assertEqual(converted['resources']['product-identity']['theme'], value['theme'])
            self.assertEqual(model.legacy_view(converted, 'application-shell')['theme'], value['theme'])
            self.assertEqual((root / plan['archive']).read_bytes(), original)
            self.assertFalse(model.resources(converted, 'frontend'))

    def test_proposal_migration_preserves_branding_and_consumer_activation_project(self):
        from composition_fixture import two_apps
        import composition_migrate as migration
        import composition_render as renderer
        graph = two_apps(ROOT)
        graph['resources']['product-identity']['theme']['branding'] = {
            'displayName': 'Harbor Workspace', 'accentColor': '#0088aa'}
        branding = model.default_branding()
        branding['theme'] = 'green'
        branding['locales']['en-GB'].update(title='Harbor Workspace', purpose='Your team schedules and rooms.',
            loadingText='Opening your workspace.', failureText='Your workspace is unavailable. Please try again.',
            noScriptText='Enable JavaScript to use your private workspace.', logoAlt='Harbor Workspace')
        branding['locales']['nl-NL'] = {**branding['locales']['en-GB'], 'title': 'Havenwerkplek'}
        graph['resources']['policy-web']['branding'] = branding
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            proposal = root / 'config/program-kit/reviewed-proposal.json'; proposal.write_text(json.dumps(graph))
            owned = root / 'tests/Activation/Activation.csproj'; owned.parent.mkdir(parents=True)
            owned.write_bytes(b'<Project><!-- consumer-owned activation tests --></Project>\n')
            original = owned.read_bytes()
            plan = migration.preview(root, 'config/program-kit/reviewed-proposal.json')
            migration.apply(root, plan['planDigest'], 'config/program-kit/reviewed-proposal.json')
            converted = model.load(root)
            self.assertEqual(converted, graph)
            self.assertEqual(converted['resources']['policy-web']['branding'], branding)
            self.assertNotIn('branding', converted['resources']['assessment-web'])
            files = renderer.materialize(root, converted, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            realm = json.loads(files['deploy/keycloak/product-identity/program-kit-realm.json'][0])
            self.assertEqual(realm['displayName'], 'Harbor Workspace')
            css = files['deploy/keycloak/product-identity/themes/program-kit/login/resources/css/program-kit.css'][0]
            self.assertIn(b'--program-kit-brand-accent: #0088aa', css)
            self.assertFalse(any(path.startswith('tests/') for path in files))
            self.assertEqual(owned.read_bytes(), original)

    def test_two_contexts_can_bind_two_databases_on_one_server(self):
        value = example()
        value['resources']['audit-db'] = {'kind': 'database', 'engine': 'postgresql', 'name': 'audit'}
        model.environment(value)['audit-db'] = {'credentialRef': 'AUDIT_PASSWORD'}
        value['bindings'].extend([
            {'kind': 'databaseServer', 'databaseRef': 'audit-db', 'serverRef': 'postgresql'},
            {'kind': 'databaseProvider', 'databaseRef': 'audit-db', 'featureRef': 'feature-1',
             'shellRef': 'application-shell', 'context': 'AuditDbContext', 'policy': 'audit'}])
        model.validate(value)
        self.assertEqual(len(model.resources(value, 'databaseServer')), 1)
        self.assertEqual(len(model.bindings(value, 'databaseProvider')), 2)

    def test_context_cannot_select_two_different_compiled_policies(self):
        value = example()
        other = deepcopy(model.bindings(value, 'databaseProvider')[0])
        other['policy'] = 'different'
        value['bindings'].append(other)
        with self.assertRaisesRegex(ValueError, 'conflicting compiled policies'):
            model.validate(value)

    def test_shared_database_role_requires_one_password_reference_per_server(self):
        value = example()
        value['resources']['audit-db'] = {'kind': 'database', 'engine': 'postgresql', 'name': 'audit'}
        env = model.environment(value)
        env['database-1']['username'] = 'shared_role'
        env['audit-db'] = {'username': 'shared_role', 'credentialRef': 'OTHER_PASSWORD'}
        value['bindings'].append({'kind': 'databaseServer', 'databaseRef': 'audit-db', 'serverRef': 'postgresql'})
        with self.assertRaisesRegex(ValueError, 'conflicting credential references'):
            model.validate(value)
        env['audit-db']['credentialRef'] = env['database-1']['credentialRef']
        model.validate(value)

    def test_same_database_requires_one_stable_resource_identity(self):
        value = example()
        value['resources']['duplicate'] = deepcopy(value['resources']['database-1'])
        model.environment(value)['duplicate'] = {'credentialRef': 'OTHER_PASSWORD'}
        value['bindings'].append({'kind': 'databaseServer', 'databaseRef': 'duplicate', 'serverRef': 'postgresql'})
        with self.assertRaisesRegex(ValueError, 'same physical database'):
            model.validate(value)

    def test_managed_and_external_database_have_different_required_properties(self):
        value = example()
        model.environment(value)['postgresql'] = {'mode': 'external', 'host': 'db.example.test', 'port': 5432}
        model.validate(value)
        model.environment(value)['postgresql'] = {'mode': 'external'}
        with self.assertRaisesRegex(ValueError, 'host and port'):
            model.validate(value)

    def test_external_identity_has_no_owned_server_or_keycloak_realm(self):
        value = example()
        model.environment(value)['product-identity'] = {'provider': 'entra', 'mode': 'external',
                                                      'issuer': 'https://login.example.test/tenant/v2.0'}
        model.validate(value)
        with self.assertRaisesRegex(ValueError, 'capability missing'):
            model.legacy_view(value, 'application-shell')

    def test_unresolved_wrong_type_and_duplicate_bindings_reject(self):
        for mutate in (
            lambda value: value['bindings'][0].update(hostRef='missing'),
            lambda value: value['bindings'][0].update(hostRef='postgresql'),
            lambda value: value['bindings'].append(deepcopy(value['bindings'][0])),
        ):
            value = example(); mutate(value)
            with self.assertRaises(ValueError):
                model.validate(value)

    def test_extra_properties_do_not_create_an_unvalidated_second_model(self):
        value = example()
        value['resources']['postgresql']['composeOverrides'] = {'image': 'latest'}
        with self.assertRaisesRegex(ValueError, 'unsupported fields'):
            model.validate(value)

    def test_each_shell_requires_explicit_host_and_one_authentication_profile(self):
        for kind in ('shellHost', 'authentication'):
            value = example()
            value['bindings'] = [row for row in value['bindings'] if row['kind'] != kind]
            with self.assertRaises(ValueError):
                model.validate(value)

    def test_callback_and_path_escape_reject_before_materialization(self):
        value = example(); value['resources']['application-shell']['source'] = '../foreign/shells.json'
        with self.assertRaises(ValueError):
            model.validate(value)
        value = example(); value['resources']['application-client']['callbackPath'] = '/../../escape'
        with self.assertRaises(ValueError):
            model.validate(value)

    def test_real_renderer_assembles_one_realm_and_three_named_contexts(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary)
            graph = two_apps(ROOT)
            result = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            realm_paths = [name for name in result if name.endswith('-realm.json')]
            self.assertEqual(len(realm_paths), 1)
            realm = json.loads(result[realm_paths[0]][0])
            self.assertEqual({row['clientId'] for row in realm['clients']},
                             {'policy-browser', 'assessment-browser', 'policy-api', 'assessment-api'})
            profile = json.loads(result['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']
            self.assertEqual(set(profile), {'policies', 'assessments'})
            for shell in profile.values():
                route = shell['Configuration']['Foundation']['HostedPages']['Routes'][0]
                self.assertEqual(route['Page'], {'Mode': 'Authenticated', 'ResponsePolicy': 'private'})
                self.assertEqual(route['Bootstrap'], route['Page'])
            self.assertEqual(set(profile['policies']['Configuration']['Foundation']['PostgreSql']['Policies']), {'policies', 'audit'})
            self.assertEqual(set(profile['assessments']['Configuration']['Foundation']['PostgreSql']['Policies']), {'assessments'})
            self.assertIn('src/Application.PostgreSql/PolicyDbContext.cs', result)
            self.assertIn('src/Application.PostgreSql/AuditDbContext.cs', result)
            self.assertNotIn('src/Application.PostgreSql/ApplicationDbContext.cs', result)
            self.assertIn(b'"audit"', result['src/Application.PostgreSql/ProviderFeature.cs'][0])
            self.assertIn('web/policy-web/package-lock.json', result)
            self.assertNotIn('__ENTRY__', result['web/policy-web/vite.config.mjs'][0].decode())

    def test_local_bff_cookie_scope_rejects_shared_hostname_before_writes(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        graph = two_apps(ROOT)
        model.environment(graph)['assessment-host']['publicOrigin'] = 'http://127.0.0.1:5001'
        with self.assertRaisesRegex(ValueError, 'ports do not isolate'):
            renderer.validate_capabilities(graph)

    def test_confidential_and_public_clients_require_distinct_credential_shapes(self):
        value = example()
        model.environment(value)['application-client']['credentialRef'] = None
        with self.assertRaisesRegex(ValueError, 'confidential client'):
            model.validate(value)
        value = example()
        value['resources']['application-client']['profile'] = 'browser-spa'
        with self.assertRaisesRegex(ValueError, 'secret-free'):
            model.validate(value)
        model.environment(value)['application-client']['credentialRef'] = None
        model.validate(value)

    def test_managed_clients_do_not_overwrite_shared_secret_or_provider_identity(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        graph = two_apps(ROOT)
        env = model.environment(graph)
        env['assessment-client']['credentialRef'] = env['application-client']['credentialRef']
        with self.assertRaisesRegex(ValueError, 'distinct credential references'):
            renderer.validate_capabilities(graph)
        graph = two_apps(ROOT)
        model.environment(graph)['application-client']['clientId'] = 'admin-cli'
        with self.assertRaisesRegex(ValueError, 'reserved Keycloak client'):
            renderer.materialize(ROOT / 'artifacts/tests/composition-model/reserved', graph,
                                 ROOT / 'extensions/program-kit-dotnet/templates/dotnet')

    def test_authority_is_validated_without_a_repository(self):
        value = example()
        value['authority'] = {'architectureMap': '../foreign.json', 'decisionIds': ['ADR-001']}
        with self.assertRaisesRegex(ValueError, 'escapes'):
            model.validate(value)
        value['authority']['architectureMap'] = 'docs/architecture/map.json'
        value['authority']['decisionIds'] = ['ADR-001', 'ADR-001']
        with self.assertRaisesRegex(ValueError, 'distinct decision'):
            model.validate(value)
        del value['authority']
        value['resources']['application-host']['ownerRef'] = 'foreign-owner'
        with self.assertRaisesRegex(ValueError, 'canonical architecture authority'):
            model.validate(value)

    def test_unqualified_environment_fails_before_any_materialization(self):
        import composition_render as renderer
        value = example()
        model.environment(value)['product-identity'] = {'provider': 'oidc', 'mode': 'external',
                                                       'issuer': 'https://login.example.test/tenant'}
        model.validate(value)
        with self.assertRaisesRegex(ValueError, 'qualified readiness adapter'):
            renderer.validate_capabilities(value)
        value = example()
        model.environment(value)['application-host'].update(publicOrigin='https://localhost:5001', certificateRef='LOCAL_CERT')
        with self.assertRaisesRegex(ValueError, 'qualified certificate adapter'):
            renderer.validate_capabilities(value)

    def test_consumer_overlay_cannot_disable_a_feature_or_weaken_private_bootstrap(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = two_apps(ROOT)
            files = renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            contract = json.loads(files[renderer.CONTRACT][0])
            shell = json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']['policies']
            selected = contract['shells']['application-shell']
            altered = deepcopy(shell)
            altered['Features'][next(iter(altered['Features']))] = False
            with self.assertRaisesRegex(ValueError, 'feature membership'):
                renderer.validate_consumer_shell(graph, 'application-shell', selected, altered, 'development')
            altered = deepcopy(shell)
            altered['Configuration']['Foundation']['HostedPages']['Routes'][0]['Bootstrap']['Mode'] = 'Public'
            with self.assertRaisesRegex(ValueError, 'hosted page access'):
                renderer.validate_consumer_shell(graph, 'application-shell', selected, altered, 'development')

    def test_shared_frontend_preserves_distinct_routes_and_permissions(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        graph = two_apps(ROOT)
        first = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
        first.update(path='/policies', pagePermission='policies.read')
        graph['bindings'].append({**first, 'routeId': 'evaluations', 'path': '/evaluations',
                                  'pagePermission': 'evaluations.read', 'bootstrapPermission': 'evaluations.details'})
        model.validate(graph)
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            files = renderer.materialize(Path(temporary), graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            shell = json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']['policies']
            routes = shell['Configuration']['Foundation']['HostedPages']['Routes']
            self.assertEqual([row['Path'] for row in routes], ['/policies', '/evaluations'])
            self.assertEqual(routes[0]['Page']['Permission'], 'policies.read')
            self.assertEqual(routes[1]['Page']['Permission'], 'evaluations.read')
            self.assertEqual(routes[1]['Bootstrap']['Permission'], 'evaluations.details')
            selected = json.loads(files[renderer.CONTRACT][0])['shells']['application-shell']
            renderer.validate_consumer_shell(graph, 'application-shell', selected, shell, 'development')
            del routes[1]['Page']['Permission']
            with self.assertRaisesRegex(ValueError, 'hosted page access'):
                renderer.validate_consumer_shell(graph, 'application-shell', selected, shell, 'development')

    def test_public_frontend_is_explicit_and_cannot_weaken_bootstrap_or_permissions(self):
        from composition_fixture import two_apps
        import composition_render as renderer
        graph = two_apps(ROOT)
        binding = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
        binding.update(pageMode='Public', bootstrapMode='Public')
        model.validate(graph)
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            files = renderer.materialize(Path(temporary), graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            shell = json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells']['policies']
            route = shell['Configuration']['Foundation']['HostedPages']['Routes'][0]
            self.assertEqual({'Mode': 'Public', 'ResponsePolicy': 'default'}, route['Page'])
            self.assertEqual({'Mode': 'Public', 'ResponsePolicy': 'default'}, route['Bootstrap'])
            selected = json.loads(files[renderer.CONTRACT][0])['shells']['application-shell']
            renderer.validate_consumer_shell(graph, 'application-shell', selected, shell, 'development')
            route['Page']['Mode'] = 'Authenticated'
            with self.assertRaisesRegex(ValueError, 'hosted page access'):
                renderer.validate_consumer_shell(graph, 'application-shell', selected, shell, 'development')
        for changes in ({'pagePermission': 'secret.read'}, {'bootstrapPermission': 'secret.read'},
                        {'pageMode': 'Authenticated'}, {'pageMode': 'anonymous'}, {'bootstrapMode': None}):
            invalid = deepcopy(graph)
            next(row for row in invalid['bindings'] if row['kind'] == 'frontend').update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'hosted page'):
                model.validate(invalid)

    def test_dynamic_page_selection_materializes_the_qualified_contract_and_rejects_overlay_drift(self):
        import composition_render as renderer
        graph = example()
        shell = graph['resources']['application-shell']
        shell['dynamicPages'] = {'Routes': [{'Id': 'stall', 'Path': '/stalls/{slug}',
            'Resolver': 'stalls', 'Mode': 'Public'}]}
        shell['presentation'] = {'enabled': True, 'settings': {'Locales': {'nl': {'sign-in': 'Aanmelden'}}, 'MaxPageBytes': 65536}}
        model.validate(graph)
        self.assertIn('Orbyss.Foundation.Web.DynamicPages', renderer.selected_packages(graph, 'application-shell'))
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            files = renderer.materialize(Path(temporary), graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            actual = json.loads(files['config/program-kit/web-profile.shells.json'][0])['CShells']['Shells'][shell['name']]
            self.assertEqual(shell['dynamicPages'], actual['Configuration']['Foundation']['DynamicPages'])
            self.assertIn('Orbyss.Foundation.Web.DynamicPages', actual['Features'])
            self.assertEqual({'nl': {'sign-in': 'Aanmelden'}}, actual['Configuration']['Foundation']['Web']['Presentation']['Locales'])
            selected = json.loads(files[renderer.CONTRACT][0])['shells']['application-shell']
            renderer.validate_consumer_shell(graph, 'application-shell', selected, actual, 'development')
            actual['Configuration']['Foundation']['DynamicPages']['Routes'][0]['Mode'] = 'Authenticated'
            with self.assertRaisesRegex(ValueError, 'dynamic page admission'):
                renderer.validate_consumer_shell(graph, 'application-shell', selected, actual, 'development')
        for invalid in (None, [], {}, ''):
            shell['dynamicPages'] = invalid
            with self.subTest(value=invalid), self.assertRaisesRegex(ValueError, 'dynamicPages'):
                model.validate(graph)

    def test_browser_plan_preserves_each_public_and_authenticated_entry_before_execution(self):
        from composition_fixture import two_apps
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
        import composition_run as run
        graph = two_apps(ROOT)
        graph['resources']['application-shell']['pathBase'] = '/market'
        first = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
        graph['bindings'].append({**first, 'routeId': 'public', 'path': '/public',
                                  'pageMode': 'Public', 'bootstrapMode': 'Public'})
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary)
            toolchain = root / 'artifacts/program-kit/toolchain.json'
            toolchain.parent.mkdir(parents=True); toolchain.write_text('{"unitFixture":true}')
            def recording_only(*args, **kwargs):
                raise RuntimeError('recorded plan; no browser or readiness claim')
            command = SimpleNamespace(environment={'PLAYWRIGHT_BROWSERS_PATH': str(root / 'browser-cache')}, run=recording_only)
            resolved = {'hosts': {'application-host': {'shells': ['application-shell'], 'publicOrigin': 'http://localhost:5001'}}}
            with self.assertRaisesRegex(RuntimeError, 'recorded plan'):
                run.browser_check(root, graph, resolved, command, root)
            host = json.loads((root / 'browser-plan.json').read_text())['hosts'][0]
            self.assertEqual('/market' + first['path'], host['page'])
            self.assertEqual([{'path': '/market' + first['path'], 'mode': 'Authenticated'},
                              {'path': '/market/public', 'mode': 'Public'}], host['entries'])

    def test_shared_frontend_rejects_ambiguous_routes_or_invalid_permissions(self):
        from composition_fixture import two_apps
        graph = two_apps(ROOT)
        first = next(row for row in graph['bindings'] if row['kind'] == 'frontend')
        for change in ({'routeId': 'other'}, {'path': '/other'}, {'pagePermission': ''}, {'bootstrapPermission': False}):
            candidate = deepcopy(graph)
            candidate['bindings'].append({**first, **change})
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'hosted page'):
                model.validate(candidate)

    def test_native_source_scope_keeps_shared_dependencies_and_excludes_other_apps(self):
        from composition_fixture import two_apps
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/scripts'))
        import runtime_closure
        graph = two_apps(ROOT, frontends=False)
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            (root / model.INPUT).parent.mkdir(parents=True, exist_ok=True)
            (root / model.INPUT).write_text(json.dumps(graph))
            projects = [{'path': row['path'], 'projectReferences': []} for row in model.resources(graph, 'feature').values()]
            core = 'src/Shared.Core/Shared.Core.csproj'
            projects.append({'path': core, 'projectReferences': []})
            build_only = 'src/Owned.Tool/Owned.Tool.csproj'
            projects.append({'path': build_only, 'projectReferences': []})
            for row in projects:
                if row['path'].endswith('.Api.csproj'):
                    row['projectReferences'] = [core]
                if row['path'].startswith('src/Assessment.Api/'):
                    row['buildProjectReferences'] = [build_only]
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').parent.mkdir(parents=True, exist_ok=True)
            (root / 'config/program-kit/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': projects}}))
            captured = {'src/Application.Api/ApiFeature.cs': 'before',
                        'src/Assessment.Api/ApiFeature.cs': 'same',
                        'src/Shared.Core/Contract.cs': 'shared', 'src/Owned.Tool/Program.cs': 'owned tool', 'global.json': 'sdk'}
            edited = {**captured, 'src/Application.Api/ApiFeature.cs': 'after'}
            stage = root / 'artifacts/runtime/assessments'
            self.assertEqual(runtime_closure.source_scope(root, stage, captured), runtime_closure.source_scope(root, stage, edited))
            changed_core = {**captured, 'src/Shared.Core/Contract.cs': 'changed'}
            self.assertNotEqual(runtime_closure.source_scope(root, stage, captured), runtime_closure.source_scope(root, stage, changed_core))
            self.assertIn('global.json', runtime_closure.source_scope(root, stage, captured))
            changed_tool = {**captured, 'src/Owned.Tool/Program.cs': 'changed build-only source'}
            self.assertNotEqual(runtime_closure.source_scope(root, stage, captured), runtime_closure.source_scope(root, stage, changed_tool))
            application_stage = root / 'artifacts/runtime/policies'
            self.assertEqual(runtime_closure.source_scope(root, application_stage, captured), runtime_closure.source_scope(root, application_stage, changed_tool))
            # The runner expands an explicit host selection to every actual
            # compilation dependant of a changed shared source.
            import composition_run
            import composition_render as renderer
            resolved = {'hosts': {name: {'runtimeStage': renderer.stage_path(host)}
                                  for name, host in model.resources(graph, 'host').items()}}
            closures = root / 'artifacts/composition/closures'; closures.mkdir(parents=True)
            for name, host in resolved['hosts'].items():
                (closures / (name + '.json')).write_text(json.dumps({'sourceInputs': runtime_closure.source_scope(root, root / host['runtimeStage'], captured)}))
            with patch.object(runtime_closure, 'source_inputs', return_value=edited):
                self.assertEqual(composition_run.affected_hosts(root, graph, resolved, ['application-host']), ['application-host'])
            with patch.object(runtime_closure, 'source_inputs', return_value=changed_core):
                self.assertEqual(composition_run.affected_hosts(root, graph, resolved, ['application-host']), ['application-host', 'assessment-host'])
            with patch.object(runtime_closure, 'source_inputs', return_value=changed_tool):
                self.assertEqual(composition_run.affected_hosts(root, graph, resolved, []), ['assessment-host'])

    def test_reviewed_proposal_population_preserves_product_and_delivery_inputs(self):
        import composition_migrate as migration
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); (root / 'scripts').mkdir(); (root / 'config/program-kit').mkdir(parents=True, exist_ok=True)
            graph = example()
            proposal = root / 'config/program-kit/reviewed-proposal.json'; proposal.write_text(json.dumps(graph))
            tasks = root / 'specs/DS01/tasks.md'; tasks.parent.mkdir(parents=True)
            tasks.write_text('- [x] T001 existing valid work\n')
            product = root / 'src/Product/Owned.cs'; product.parent.mkdir(parents=True)
            product.write_text('consumer implementation')
            plan = migration.preview(root, 'config/program-kit/reviewed-proposal.json')
            tasks.write_text('- [x] T001 newer valid work\n')
            with self.assertRaisesRegex(ValueError, 'stale'):
                migration.apply(root, plan['planDigest'], 'config/program-kit/reviewed-proposal.json')
            plan = migration.preview(root, 'config/program-kit/reviewed-proposal.json')
            migration.apply(root, plan['planDigest'], 'config/program-kit/reviewed-proposal.json')
            self.assertEqual(model.load(root), graph)
            self.assertEqual(product.read_text(), 'consumer implementation')
            self.assertEqual(tasks.read_text(), '- [x] T001 newer valid work\n')
            self.assertEqual(json.loads((root / plan['archive']).read_text()), graph)


if __name__ == '__main__':
    unittest.main(verbosity=2)
