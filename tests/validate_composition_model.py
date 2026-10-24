"""Pure typed-resource invariants and preservation at the legacy import boundary."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import composition_model as model


def example():
    value = json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak-postgresql.json').read_text())
    return model.from_legacy(value)


class ResourceModel(unittest.TestCase):
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
            profile = json.loads(files['eng/web-profile.shells.json'][0])
            shell = graph['resources']['application-shell']['name']
            configuration = profile['CShells']['Shells'][shell]['Configuration']
            self.assertEqual('products/orders', configuration['WebRouting']['Path'])
            contract = json.loads(files['eng/foundation-settings.contract.json'][0])
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
        contract = json.loads(files['eng/foundation-settings.contract.json'][0])
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
        ownership = json.loads(files['eng/architecture.json'][0])['runtimeComposition']['projects']
        self.assertEqual(['owned runtime capability registration'], next(row for row in ownership if row['path'] ==
                         'src/Evidence.Files/Evidence.Files.csproj')['responsibilities'][0]['effects'])

    def test_reviewed_runtime_provider_is_not_coerced_to_persistence(self):
        graph = self.ordinary_provider_graph(declared=False)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / 'eng').mkdir()
            (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [{
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
            (root / 'eng').mkdir()
            owned = {'path': runtime['path'], 'role': 'implementation', 'projectReferences': [],
                     'packageReferences': ['CShells.Abstractions', 'Orbyss.Foundation.Execution'],
                     'responsibilities': [{'name': 'PolicyPortfolio.Lifecycle', 'kind': 'runtime',
                                           'effects': ['owned policy effects']}]}
            (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': [owned]}}))
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
            generated = json.loads(files['eng/architecture.json'][0])['runtimeComposition']['projects']
            self.assertEqual(next(row for row in generated if row['path'] == runtime['path'])['responsibilities'], owned['responsibilities'])
            activations = json.loads(files['eng/web-profile.shells.json'][0])['CShells']['Shells']['default']['Features']
            self.assertIn(runtime['featureIdentity'], activations)
            obsolete = root / 'src/PolicyPortfolio/ApiFeature.cs'
            obsolete.parent.mkdir(parents=True)
            previous = b'[ShellFeature("Existing.PolicyIdentity")] public sealed class ApiFeature : IWebShellFeature { /* owned registration */ }'
            obsolete.write_bytes(previous)
            with self.assertRaisesRegex(ValueError, 'retained customized API seam'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            self.assertEqual(obsolete.read_bytes(), previous)
            obsolete.write_bytes(previous.replace(b'IWebShellFeature', b'IShellFeature'))
            with self.assertRaisesRegex(ValueError, 'retained customized API seam'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            obsolete.write_bytes(previous)
            state = root / '.program-kit/managed.json'; state.parent.mkdir()
            import hashlib
            state.write_text(json.dumps({'files': {'src/PolicyPortfolio/ApiFeature.cs': {
                'ownership': 'scaffold', 'contribution': 'foundation',
                'sourceIdentity': '../../scripts/foundation_composition.py',
                'baselineHash': hashlib.sha256(previous).hexdigest()}}}))
            renderer.admit_runtime_reconciliation(root, model.project_definition(runtime, root))
            state.unlink(); obsolete.unlink()
            runtime['capabilityPackages'] = ['Orbyss.Foundation.Unselected']
            with self.assertRaisesRegex(ValueError, 'absent from selected shell'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
            runtime['capabilityPackages'] = ['Orbyss.Foundation.Execution']
            runtime['responsibility'] = 'http'
            with self.assertRaisesRegex(ValueError, 'conflicts with source authority'):
                renderer.materialize(root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')

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
                return json.loads(files['eng/web-profile.shells.json'][0])['CShells']['Shells']['default']['Configuration']['Foundation']['Web']
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
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
        import release_bundle
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example()
            graph['resources']['page'] = {'kind': 'frontend', 'directory': 'web/page', 'entry': 'src/app.ts'}
            graph['bindings'].append({'kind': 'frontend', 'frontendRef': 'page', 'shellRef': 'application-shell', 'routeId': 'page', 'path': '/'})
            shutil.copytree(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng', root / 'eng')
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
            profile = root / 'eng/web-profile.shells.json'; profile.write_bytes(profile.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'managed composition output changed'):
                release_bundle.typed_publisher_features(root, {identity})

    def test_native_sync_reconciles_untouched_runtime_scaffold_and_preserves_custom_project(self):
        import subprocess
        import xml.etree.ElementTree as ET
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); graph = example(); (root / 'eng').mkdir()
            input_path = root / model.INPUT; input_path.write_text(json.dumps(graph))
            command = [sys.executable, str(ROOT / 'extensions/program-kit-dotnet/scripts/dotnet_sync.py'),
                       '--target', str(root), '--profile-selected', '--foundation-host-accepted',
                       '--building-block-sources-approved', '--web-profile', 'bff-cookie', '--json']
            def sync():
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            sync()
            pins = {path: (root / path).read_bytes() for path in ('eng/ProgramKit.Foundation.props', 'eng/ProgramKit.Packages.props')}
            project = graph['resources']['feature-0']
            project['capabilityPackages'] = ['Orbyss.Foundation.Execution']
            input_path.write_text(json.dumps(graph)); sync()
            self.assertIn('Orbyss.Foundation.Execution', (root / Path(project['path']).parent / 'ApiFeature.cs').read_text())
            project['capabilityPackages'] = []; project['responsibility'] = 'runtime'
            input_path.write_text(json.dumps(graph))
            architecture_path = root / 'eng/architecture.json'
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
            generated = {row.get('Include') for row in ET.fromstring(files['eng/ProgramKit.Foundation.props'][0]).iter('PackageVersion')}
            self.assertTrue(native)
            self.assertFalse(native & generated)
            self.assertNotIn('eng/ProgramKit.BuildingBlocks.props', files)
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
            root = Path(temporary); (root / 'eng').mkdir()
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
            root = Path(temporary); (root / 'eng').mkdir()
            proposal = root / 'eng/reviewed-proposal.json'; proposal.write_text(json.dumps(graph))
            owned = root / 'tests/Activation/Activation.csproj'; owned.parent.mkdir(parents=True)
            owned.write_bytes(b'<Project><!-- consumer-owned activation tests --></Project>\n')
            original = owned.read_bytes()
            plan = migration.preview(root, 'eng/reviewed-proposal.json')
            migration.apply(root, plan['planDigest'], 'eng/reviewed-proposal.json')
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
            profile = json.loads(result['eng/web-profile.shells.json'][0])['CShells']['Shells']
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
            shell = json.loads(files['eng/web-profile.shells.json'][0])['CShells']['Shells']['policies']
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
            shell = json.loads(files['eng/web-profile.shells.json'][0])['CShells']['Shells']['policies']
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
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
        import runtime_closure
        graph = two_apps(ROOT, frontends=False)
        scratch = ROOT / 'artifacts/tests/composition-model'; scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary); (root / 'eng').mkdir()
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
            (root / 'eng/architecture.json').write_text(json.dumps({'runtimeComposition': {'projects': projects}}))
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
            root = Path(temporary); (root / 'eng').mkdir()
            graph = example()
            proposal = root / 'eng/reviewed-proposal.json'; proposal.write_text(json.dumps(graph))
            tasks = root / 'specs/DS01/tasks.md'; tasks.parent.mkdir(parents=True)
            tasks.write_text('- [x] T001 existing valid work\n')
            product = root / 'src/Product/Owned.cs'; product.parent.mkdir(parents=True)
            product.write_text('consumer implementation')
            plan = migration.preview(root, 'eng/reviewed-proposal.json')
            tasks.write_text('- [x] T001 newer valid work\n')
            with self.assertRaisesRegex(ValueError, 'stale'):
                migration.apply(root, plan['planDigest'], 'eng/reviewed-proposal.json')
            plan = migration.preview(root, 'eng/reviewed-proposal.json')
            migration.apply(root, plan['planDigest'], 'eng/reviewed-proposal.json')
            self.assertEqual(model.load(root), graph)
            self.assertEqual(product.read_text(), 'consumer implementation')
            self.assertEqual(tasks.read_text(), '- [x] T001 newer valid work\n')
            self.assertEqual(json.loads((root / plan['archive']).read_text()), graph)


if __name__ == '__main__':
    unittest.main(verbosity=2)
