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
sys.path[:0] = [str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(TEMPLATE / 'files/eng')]
import composition_model as model
import composition_migrate as migrate
import composition_render as render
import openapi_pipeline as pipeline
import toolchain
from composition_fixture import two_apps


class MigratedTooling(unittest.TestCase):
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
        self.graph['resources']['product-identity']['theme']['branding']['displayName'] = 'Claim Evaluator'
        branding = model.default_branding()
        branding['locales']['en-GB'].update(title='Claim Evaluator', purpose='Consumer-owned claims',
            loadingText='Loading claims.', failureText='Claims could not be loaded.')
        self.graph['resources']['policy-web']['branding'] = branding
        (self.root / 'proposal.json').write_text(json.dumps(self.graph))
        (self.root / 'eng').mkdir()
        shutil.copytree(TEMPLATE / 'files/eng', self.root / 'eng', dirs_exist_ok=True)
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
        defaults = json.loads((self.root / 'eng/openapi-defaults.json').read_text())
        defaults['compatibility']['version'] = '1.29.1'
        (self.root / 'eng/openapi-defaults.json').write_text(json.dumps(defaults))
        with patch.object(sys, 'argv', ['openapi_init', '--repository', str(self.root), '--identity', 'only',
                '--document-name', 'v1', '--shell', 'default', '--feature', 'Application.Api',
                '--application-directory', 'web', '--application-tsconfig', 'web/tsconfig.json']):
            self.assertEqual(0, openapi_init.main())
        contract = json.loads((self.root / 'contracts/openapi/only.contract.json').read_text())
        self.assertEqual('1.33.0', contract['compatibility']['oasdiffVersion'])
        self.assertEqual('artifacts/runtime/only/packages', contract['packageClosure'])
        self.assertEqual('1.29.1', json.loads((self.root / 'eng/openapi-defaults.json').read_text())['compatibility']['version'])
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
        import artifact_ownership
        feature = self.root / 'specs/003-openapi'; feature.mkdir(parents=True)
        (feature / 'plan.md').write_text('OpenAPI Application.Api is exported from its unique host stage.')
        with patch.object(artifact_ownership, 'repository_root', return_value=self.root):
            artifact_ownership.validate_openapi_pipeline(feature, {'profiles': ['dotnet']}, False)
            contract['packageClosure'] = 'artifacts/release-bundle/packages'
            (self.root / 'contracts/openapi/only.contract.json').write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValueError, 'validated host closure'):
                artifact_ownership.validate_openapi_pipeline(feature, {'profiles': ['dotnet']}, False)

    def test_typed_persona_script_loads_migrated_realm_and_rejects_extra_users(self):
        suite = self.root / 'eng/web'
        shutil.copyfile(TEMPLATE / 'web-profiles/common/eng/web/persona-fixture.ts', suite / 'persona-fixture.ts')
        package = json.loads((TEMPLATE / 'web-profiles/common/eng/web/package.json').read_text())
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
        registry = self.root / 'eng/openapi-contracts.json'
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
        self.assertEqual('Claim Evaluator', realm['displayName'])
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
