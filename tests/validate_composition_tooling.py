"""Focused migrated-consumer tooling contracts; no agent or paid provider."""
from copy import deepcopy
from types import SimpleNamespace
import json
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
import os
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(TEMPLATE / 'files/scripts')]
import composition_model as model
import composition_migrate as migrate
import composition_render as render
import openapi_pipeline as pipeline
import toolchain
from composition_fixture import two_apps


class MigratedTooling(unittest.TestCase):
    def test_browser_preparation_uses_durable_helper_owner(self):
        import composition_run as runner
        from unittest.mock import Mock
        command = Mock()
        with patch.object(runner.qualification, 'npm_command', return_value=(['npm', 'ci'], {})), \
             patch.object(runner.qualification, 'playwright_command', return_value=['node', 'fixture-playwright']), \
             patch.object(runner, 'browser_check'):
            runner.prepare_browsers(self.root, self.graph, {}, command, self.root / 'artifacts/browser')
        self.assertEqual(self.root / 'tools/program-kit/web', command.run.call_args_list[0].kwargs['cwd'])

    def test_configuration_environment_projection_is_ephemeral_and_preflights_before_native_effects(self):
        import composition_run as run
        from collections import defaultdict
        feature = next(iter(model.resources(self.graph, 'feature')))
        shell = next(row['shellRef'] for row in model.bindings(self.graph, 'featureShell') if row['featureRef'] == feature)
        self.graph['bindings'].append({'kind': 'configurationEnvironment', 'featureRef': feature, 'shellRef': shell,
            'setting': 'Example:HmacSecret', 'environmentRef': 'PK_TEST_PRODUCT_HMAC'})
        model.validate(self.graph)
        binding = model.configuration_environment_bindings(self.graph)[0]
        declaration = run.configuration_environment_contract(self.root, self.graph)[0]
        self.assertEqual('native-declaration-not-present', declaration['sourceDeclaration'])
        self.assertIn('Declarative integration only', declaration['proof'])
        contract = json.loads((self.root / render.CONTRACT).read_text())
        resolved = json.loads((self.root / render.RESOLVED).read_text())
        with patch.dict(os.environ, {'PK_TEST_PRODUCT_HMAC': 'synthetic-hmac-value'}):
            supplied = run.configuration_environment_values(self.root, self.graph)
            credentials = defaultdict(lambda: 'synthetic-native-value')
            document, environment = run.compose_model(self.root, self.graph, contract, resolved, credentials,
                                                       product_inputs=supplied)
        service = document['services'][run.service(binding['hostRef'])]
        placeholder = service['environment'][binding['environmentKey']]
        self.assertTrue(placeholder.startswith('${PKC_'))
        self.assertNotIn('synthetic-hmac-value', json.dumps(document))
        self.assertIn('synthetic-hmac-value', environment.values())
        self.assertFalse((self.root / 'artifacts/composition/private/credentials.json').exists())
        fingerprint = run.topology_fingerprint(self.root, self.graph, contract)
        with patch.dict(os.environ, {'PK_TEST_PRODUCT_HMAC': 'synthetic-hmac-value'}):
            run.private_credentials(self.root, self.graph, create=True)
        private = self.root / 'artifacts/composition/private/credentials.json'
        retained = private.read_bytes()
        self.assertNotIn(b'synthetic-hmac-value', retained)
        self.assertNotIn(b'PK_TEST_PRODUCT_HMAC', retained)
        with patch.dict(os.environ, {'PK_TEST_PRODUCT_HMAC': 'synthetic-rotated-hmac'}):
            fresh = run.private_credentials(self.root, self.graph)
            _, environment = run.compose_model(self.root, self.graph, contract, resolved, fresh)
        self.assertIn('synthetic-rotated-hmac', environment.values())
        self.assertNotIn('synthetic-hmac-value', environment.values())
        self.assertEqual(retained, private.read_bytes())
        self.assertEqual(fingerprint, run.topology_fingerprint(self.root, self.graph, contract))
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(run, 'selected', return_value=(self.graph, contract, resolved)), \
             patch.object(run, 'Commands', side_effect=AssertionError('No native process before product input admission')):
            with self.assertRaisesRegex(ValueError, 'required product configuration environment input is missing: PK_TEST_PRODUCT_HMAC'):
                run.prepare(self.root)

    def test_product_input_and_native_credential_namespaces_remain_independent_across_rotation(self):
        import composition_run as run
        authority = next(iter(model.resources(self.graph, 'identityAuthority')))
        native_key = run.variable('identity-admin:' + authority)
        feature = next(iter(model.resources(self.graph, 'feature')))
        shell = next(row['shellRef'] for row in model.bindings(self.graph, 'featureShell') if row['featureRef'] == feature)
        row = {'kind': 'configurationEnvironment', 'featureRef': feature, 'shellRef': shell,
               'setting': 'Example:HmacSecret', 'environmentRef': native_key}
        self.graph['bindings'].append(row)
        contract = json.loads((self.root / render.CONTRACT).read_text())
        resolved = json.loads((self.root / render.RESOLVED).read_text())
        private_path = self.root / 'artifacts/composition/private/credentials.json'
        native_value = None
        retained = None
        for reference in (native_key, native_key.lower()):
            row['environmentRef'] = reference
            model.validate(self.graph)
            for product_value in ('synthetic-product-before-rotation', 'synthetic-product-after-rotation'):
                # Supply both spellings with the same value: Windows treats
                # environment names case-insensitively; POSIX remains explicit.
                with self.subTest(reference=reference, product_value=product_value), \
                     patch.dict(os.environ, {native_key: product_value, native_key.lower(): product_value}):
                    supplied = run.configuration_environment_values(self.root, self.graph)
                    credentials = run.private_credentials(self.root, self.graph, create=retained is None)
                    if retained is None:
                        retained = private_path.read_bytes()
                        native_value = json.loads(retained)[native_key]
                    self.assertEqual(native_value, credentials[native_key])
                    self.assertNotEqual(product_value, native_value)
                    self.assertEqual(product_value, supplied[reference])
                    document, environment = run.compose_model(self.root, self.graph, contract, resolved,
                                                               credentials, product_inputs=supplied)
                    binding = model.configuration_environment_bindings(self.graph)[0]
                    product_key = run.variable('configuration:' + shell + ':' + binding['configurationKey'].casefold())
                    self.assertEqual(product_value, environment[product_key])
                    self.assertEqual(native_value, environment[native_key])
                    # Ambient callers receive the same safe separation.
                    self.assertEqual(environment, run.compose_model(self.root, self.graph, contract, resolved, credentials)[1])
                    self.assertEqual(retained, private_path.read_bytes())
                    self.assertNotIn(product_value, json.dumps(document))
                    self.assertNotIn(product_value.encode(), retained)

    def test_declared_external_inputs_invalidate_frontend_and_only_its_host(self):
        import prepare_hosted_pages as frontend
        graph = deepcopy(self.graph)
        graph['resources']['policy-web']['inputs'] = ['docs/brand', 'src/SharedWeb/theme.css']
        (self.root / model.INPUT).write_text(json.dumps(graph))
        for name in ('.nvmrc', '.npm-version'):
            shutil.copyfile(TEMPLATE / 'files' / name, self.root / name)
        folder = self.root / 'docs/brand'; folder.mkdir(parents=True)
        (folder / 'logo.png').write_bytes(b'synthetic-logo')
        shared = self.root / 'src/SharedWeb/theme.css'; shared.parent.mkdir(parents=True); shared.write_text('body {}')
        before = frontend.input_snapshot(self.root, graph, 'policy-web')
        source = {'docs/brand/logo.png': 'first', 'src/SharedWeb/theme.css': 'theme'}
        selected = pipeline.runtime_closure.source_scope(self.root, self.root / 'artifacts/runtime/policies', source)
        other = pipeline.runtime_closure.source_scope(self.root, self.root / 'artifacts/runtime/assessments', source)
        self.assertEqual(source, selected)
        self.assertEqual({}, other)
        (folder / 'logo.png').write_bytes(b'changed-logo')
        self.assertNotEqual(before, frontend.input_snapshot(self.root, graph, 'policy-web'))
        (folder / 'added.css').write_text('html {}')
        added = frontend.input_snapshot(self.root, graph, 'policy-web')
        self.assertIn('docs/brand/added.css', added)
        (folder / 'logo.png').unlink()
        self.assertNotIn('docs/brand/logo.png', frontend.input_snapshot(self.root, graph, 'policy-web'))
        shared.unlink()
        with self.assertRaisesRegex(ValueError, 'declared source input is missing'):
            frontend.input_snapshot(self.root, graph, 'policy-web')

    def test_declared_external_inputs_and_actual_theme_tree_bind_preparation(self):
        import composition_run as run
        contract = json.loads((self.root / render.CONTRACT).read_text())
        before = run.topology_fingerprint(self.root, self.graph, contract)
        theme = self.root / 'deploy/keycloak/product-identity/themes/program-kit/login/resources/css/product.css'
        theme.write_text('body { color: blue; }')
        changed = run.topology_fingerprint(self.root, self.graph, contract)
        self.assertNotEqual(before, changed)
        theme.unlink()
        self.assertEqual(before, run.topology_fingerprint(self.root, self.graph, contract))
        self.graph['resources']['product-identity']['inputs'] = ['docs/brand']
        brand = self.root / 'docs/brand'; brand.mkdir(parents=True)
        logo = brand / 'logo.png'; logo.write_bytes(b'synthetic-original')
        before = run.topology_fingerprint(self.root, self.graph, contract)
        logo.write_bytes(b'synthetic-new')
        self.assertNotEqual(before, run.topology_fingerprint(self.root, self.graph, contract))
        logo.unlink()
        self.assertNotEqual(before, run.topology_fingerprint(self.root, self.graph, contract))

    def test_reviewed_comparator_is_available_before_first_emitted_build(self):
        import validate_composition_start as fixture
        self.root.joinpath('.oasdiff-version').write_text('1.33.0\n')
        # A deliberately renamed source checks canonical staging; a successful
        # version probe is not evidence that this fictional comparator diffs APIs.
        source = self.root / ('reviewed.cmd' if os.name == 'nt' else 'reviewed')
        source.write_text('@echo oasdiff 1.33.0\n' if os.name == 'nt' else '#!/bin/sh\necho oasdiff 1.33.0\n')
        if os.name != 'nt':
            source.chmod(0o755)
        staged = fixture.prepare_comparison_tool(self.root, source)
        self.assertEqual('oasdiff.cmd' if os.name == 'nt' else 'oasdiff', staged.name)
        self.assertEqual(source.read_bytes(), staged.read_bytes())
        if os.name != 'nt':
            self.assertTrue(os.access(staged, os.X_OK), 'Staging must retain POSIX execution permission')
        self.assertEqual((staged, '1.33.0'), toolchain.resolve_oasdiff(self.root, '1.33.0', ''))
        self.root.joinpath('.oasdiff-version').write_text('0.0.0\n')
        with self.assertRaisesRegex(ValueError, 'PKT021'):
            fixture.prepare_comparison_tool(self.root, source)

    def test_typed_flow_missing_public_problem_contract_stops_before_fixture_or_native_effects(self):
        import dependency_profile
        import validate_composition_start as fixture
        resolver = SimpleNamespace(new_project_catalog=lambda: {'families': {'foundation': {'releaseVersion': '0.3.5'}}})
        with patch.object(sys, 'argv', ['validate_composition_start.py', '--execute', '--single-host', '--tooling', '--oasdiff', sys.executable]), \
             patch.object(dependency_profile, 'resolver', return_value=resolver), \
             patch.object(fixture, 'install_native_tooling', side_effect=AssertionError('No native installation before public dependency admission')), \
             patch.object(fixture, 'two_apps', side_effect=AssertionError('No graph or runtime effects before public dependency admission')):
            with self.assertRaisesRegex(ValueError, 'released Foundation public problem wire contract.*qualified default profile'):
                fixture.main()

    def setUp(self):
        scratch = ROOT / 'artifacts/tests/composition-tooling'; scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.graph = two_apps(ROOT)
        self.graph['resources']['product-identity']['theme']['branding']['displayName'] = 'Harbor Workspace'
        branding = model.default_branding()
        branding['locales']['en-GB'].update(title='Harbor Workspace', purpose='Consumer-owned room schedules',
            loadingText='Loading claims.', failureText='Claims could not be loaded.')
        self.graph['resources']['policy-web']['branding'] = branding
        (self.root / 'proposal.json').write_text(json.dumps(self.graph))
        (self.root / 'scripts').mkdir()
        shutil.copytree(TEMPLATE / 'files/scripts', self.root / 'scripts', dirs_exist_ok=True)
        shutil.copytree(TEMPLATE / 'files/tools', self.root / 'tools', dirs_exist_ok=True)
        shutil.copytree(TEMPLATE / 'files/.config', self.root / '.config', dirs_exist_ok=True)
        shutil.copytree(TEMPLATE / 'files/config', self.root / 'config', dirs_exist_ok=True)
        self.retained = {
            'src/Existing/Custom.cs': b'// Existing owned implementation stays intact.\n',
            'src/Existing/packages.lock.json': b'{"historical-lock":"exact-retained-bytes"}\n',
            'specs/002-policies/tasks.md': b'T007 prerequisite; T008/T009 behavior; T012 Affected; effort 120; human pending.\n',
            'artifacts/proofs/historical.json': b'{"status":"passed","historical":true}\n',
        }
        for name, payload in self.retained.items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
        plan = migrate.preview(self.root, 'proposal.json')
        migrate.apply(self.root, plan['planDigest'], 'proposal.json')
        for name, (payload, _) in render.materialize(self.root, self.graph, TEMPLATE).items():
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)

    def test_export_selects_each_unique_host_and_retains_legacy(self):
        for shell, host, stage in [('policies', 'application-host', 'runtime/policies'),
                                   ('assessments', 'assessment-host', 'runtime/assessments')]:
            packages, evidence = pipeline.runtime_target(self.root, shell)
            self.assertEqual('artifacts/' + stage + '/packages', packages)
            self.assertEqual(self.root / 'artifacts/composition/closures' / (host + '.json'), evidence)
        (self.root / model.INPUT).unlink()
        self.assertEqual(('artifacts/release-bundle/packages', self.root / pipeline.runtime_closure.EVIDENCE),
                         pipeline.runtime_target(self.root, 'legacy'))

    def test_single_host_initialization_uses_adopted_pin_not_stale_defaults(self):
        import openapi_init
        graph = model.from_legacy(json.loads((TEMPLATE / 'compositions/foundation-bff-keycloak.json').read_text()))
        graph['resources']['application-host']['runtimeDirectory'] = 'runtime/only'
        graph['resources']['application-shell']['source'] = 'runtime/only/shells.json'
        (self.root / model.INPUT).write_text(json.dumps(graph))
        for name, (payload, _) in render.materialize(self.root, graph, TEMPLATE).items():
            target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
        (self.root / '.oasdiff-version').write_text('1.33.0\n')
        defaults = json.loads((self.root / 'scripts/openapi-defaults.json').read_text())
        defaults['compatibility']['version'] = '1.29.1'
        (self.root / 'scripts/openapi-defaults.json').write_text(json.dumps(defaults))
        with patch.object(sys, 'argv', ['openapi_init', '--repository', str(self.root), '--identity', 'only',
                '--document-name', 'v1', '--shell', 'default', '--feature', 'Application.Api',
                '--application-directory', 'web', '--application-tsconfig', 'web/tsconfig.json']):
            self.assertEqual(0, openapi_init.main())
        contract = json.loads((self.root / 'contracts/openapi/only.contract.json').read_text())
        self.assertEqual('1.33.0', contract['compatibility']['oasdiffVersion'])
        self.assertEqual('artifacts/runtime/only/packages', contract['packageClosure'])
        self.assertEqual('1.29.1', json.loads((self.root / 'scripts/openapi-defaults.json').read_text())['compatibility']['version'])
        manifest = json.loads((self.root / '.config/dotnet-tools.json').read_text())
        exporter = manifest['tools']['orbyss.foundation.openapi.exporter']['version']
        contract_path = self.root / 'contracts/openapi/only.contract.json'
        validated, paths = pipeline.validate_contract(self.root, contract_path, exporter, '1.33.0')
        self.assertEqual(contract, validated)
        self.assertEqual(self.root / 'artifacts/runtime/only/packages', paths['packages'])
        self.assertEqual(self.root / 'artifacts/composition/closures/application-host.json',
                         paths['closureEvidence'])
        contract['packageClosure'] = 'artifacts/release-bundle/packages'
        contract_path.write_text(json.dumps(contract))
        with self.assertRaisesRegex(ValueError, 'PKO204 packageClosure must be the exact validated stage'):
            pipeline.validate_contract(self.root, contract_path, exporter, '1.33.0')
        for name, payload in self.retained.items():
            self.assertEqual(payload, (self.root / name).read_bytes())

    def test_typed_persona_script_loads_migrated_realm_and_rejects_extra_users(self):
        suite = self.root / 'tools/program-kit/web'
        shutil.copyfile(TEMPLATE / 'web-profiles/common/tools/program-kit/web/persona-fixture.ts', suite / 'persona-fixture.ts')
        package = json.loads((TEMPLATE / 'web-profiles/common/tools/program-kit/web/package.json').read_text())
        self.assertIn("import('./persona-fixture.ts')", package['scripts']['test:fixture'])
        realm = self.root / 'deploy/keycloak/product-identity/program-kit-realm.json'
        document = json.loads(realm.read_text())
        import os
        environment = {**os.environ, 'PROGRAMKIT_IDENTITY_REALM_FILE': str(realm),
                       'PROGRAMKIT_IDENTITY_AUTHORITY': 'http://localhost:8080/realms/program-kit'}
        command = ['node', '--input-type=module', '-e', "await import('./persona-fixture.ts')"]
        loaded = subprocess.run(command, cwd=suite, env=environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(0, loaded.returncode, loaded.stderr)
        document['users'].append(deepcopy(document['users'][0]))
        realm.write_text(json.dumps(document))
        rejected = subprocess.run(command, cwd=suite, env=environment, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(0, rejected.returncode)
        self.assertIn('exactly the three governed personas', rejected.stderr)
        for user in document['users']:
            for credential in user['credentials']:
                self.assertNotIn(credential['value'], loaded.stdout + loaded.stderr + rejected.stdout + rejected.stderr)

    def test_initializer_rejects_missing_or_malformed_pin_without_partial_writes(self):
        import openapi_init
        registry = self.root / 'config/program-kit/openapi-contracts.json'
        original_registry = registry.read_bytes()
        arguments = ['openapi_init', '--repository', str(self.root), '--identity', 'invalid-pin',
                     '--document-name', 'v1', '--shell', 'policies', '--feature', 'Application.Api',
                     '--application-directory', 'web', '--application-tsconfig', 'web/tsconfig.json']
        for value in (None, '', 'latest', '1.33.0\n1.29.1'):
            pin = self.root / '.oasdiff-version'
            if value is None: pin.unlink(missing_ok=True)
            else: pin.write_text(value)
            with self.subTest(pin=value), patch.object(sys, 'argv', arguments):
                self.assertEqual(2, openapi_init.main())
                self.assertEqual(original_registry, registry.read_bytes())
                self.assertFalse((self.root / 'contracts/openapi/invalid-pin.contract.json').exists())
                self.assertFalse((self.root / 'tools/openapi/invalid-pin').exists())

    def test_unknown_ambiguous_and_stale_composition_reject(self):
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            pipeline.runtime_target(self.root, 'unknown')
        graph = deepcopy(self.graph)
        graph['bindings'].append({'kind': 'shellHost', 'shellRef': 'application-shell', 'hostRef': 'assessment-host'})
        (self.root / model.INPUT).write_text(json.dumps(graph))
        with self.assertRaises(ValueError):
            pipeline.runtime_target(self.root, 'policies')
        (self.root / model.INPUT).write_text(json.dumps(self.graph))
        (self.root / render.RESOLVED).write_text('{}')
        with self.assertRaises(ValueError):
            pipeline.runtime_target(self.root, 'policies')

    def test_migration_keeps_consumer_branding_and_provider_metadata(self):
        graph = model.load(self.root)
        self.assertEqual(self.graph['resources']['policy-web']['branding'], graph['resources']['policy-web']['branding'])
        realm = json.loads((self.root / 'deploy/keycloak/product-identity/program-kit-realm.json').read_text())
        self.assertEqual('Harbor Workspace', realm['displayName'])
        provider = ET.parse(self.root / 'src/Application.PostgreSql/Application.PostgreSql.csproj')
        self.assertEqual('false', provider.findtext('PropertyGroup/FoundationComposeForOpenApi'))
        self.assertIn('AddFoundationPostgreSql', (self.root / 'src/Application.PostgreSql/ProviderFeature.cs').read_text())
        for name, payload in self.retained.items():
            self.assertEqual(payload, (self.root / name).read_bytes())

    def test_export_checks_host_evidence_before_producer(self):
        packages, evidence = pipeline.runtime_target(self.root, 'policies')
        paths = {'packages': self.root / packages, 'closureEvidence': evidence}
        contract = {'identity': 'policies'}
        with patch.object(pipeline.runtime_closure, 'validate', side_effect=ValueError('wrong-stage or stale evidence')) as validation, \
                patch.object(pipeline, 'run') as producer:
            with self.assertRaisesRegex(ValueError, 'wrong-stage'):
                pipeline.execute_contract(self.root, self.root / 'contract.json', contract, paths, None,
                    'dotnet', self.root / 'toolchain.json', 'oasdiff', {}, False, False, self.root / 'shells.json')
            self.assertEqual(evidence, validation.call_args.args[2])
            producer.assert_not_called()


class OwnerFixtureCleanup(unittest.TestCase):
    """Failed setup must never become positive cleanup evidence."""

    def test_no_preparation_does_not_claim_disposal(self):
        import io
        import time
        from unittest.mock import Mock
        from composition_owner_fixture import finish_owner_operation
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); dispose = Mock()
            result = {'status': 'failed', 'budgetSeconds': 300}
            with patch('sys.stdout', new=io.StringIO()):
                finish_owner_operation(root, None, root, dispose, result, time.monotonic())
            sealed = json.loads((root / 'result.json').read_text())
            dispose.assert_not_called()
            self.assertFalse(sealed['cleanupAttempted'])
            self.assertIsNone(sealed['cleanupComplete'])
            self.assertEqual('unverified-no-successful-preparation', sealed['cleanupDisposition'])
            self.assertEqual('failed', sealed['status'])

    def test_successful_disposal_is_observed(self):
        import io
        import time
        from unittest.mock import Mock
        from composition_owner_fixture import finish_owner_operation
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); dispose = Mock(); preparation = {'project': 'fictional-project'}
            result = {'status': 'passed', 'budgetSeconds': 300}
            with patch('sys.stdout', new=io.StringIO()):
                finish_owner_operation(root, preparation, root, dispose, result, time.monotonic())
            sealed = json.loads((root / 'result.json').read_text())
            dispose.assert_called_once_with(root, preparation, root / 'dispose')
            self.assertTrue(sealed['cleanupAttempted'])
            self.assertTrue(sealed['cleanupComplete'])
            self.assertEqual('completed', sealed['cleanupDisposition'])
            self.assertEqual('passed', sealed['status'])

    def test_disposal_failure_still_seals_failed_result(self):
        import io
        import time
        from unittest.mock import Mock
        from composition_owner_fixture import finish_owner_operation
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); dispose = Mock(side_effect=RuntimeError('synthetic disposal failure'))
            result = {'status': 'passed', 'budgetSeconds': 300}
            with patch('sys.stdout', new=io.StringIO()), self.assertRaisesRegex(RuntimeError, 'synthetic disposal failure'):
                finish_owner_operation(root, {'project': 'fictional-project'}, root, dispose, result, time.monotonic())
            sealed = json.loads((root / 'result.json').read_text())
            self.assertTrue(sealed['cleanupAttempted'])
            self.assertFalse(sealed['cleanupComplete'])
            self.assertEqual('failed', sealed['cleanupDisposition'])
            self.assertEqual('failed', sealed['status'])
            self.assertIn('elapsedSeconds', sealed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
