"""Selected native realm resolution and real maintained TypeScript persona loading."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(TEMPLATE / 'files/scripts')]
import validate_composition_tooling as tooling
import composition_model as model
import composition_render as render
import web_identity


class SelectedIdentity(unittest.TestCase):
    setUp = tooling.MigratedTooling.setUp
    def persona(self, environment):
        suite = self.root / 'eng/web'
        shutil.copyfile(TEMPLATE / 'web-profiles/common/tools/program-kit/web/persona-fixture.ts', suite / 'persona-fixture.ts')
        selected = {key: value for key, value in os.environ.items() if not key.startswith('PROGRAMKIT_IDENTITY_')}
        return subprocess.run(['node', '--input-type=module', '-e', "await import('./persona-fixture.ts')"],
                              cwd=suite, env={**selected, **environment}, capture_output=True, text=True, timeout=30)

    def test_two_distinct_identity_resources_realms_and_selected_authority(self):
        for resource, realm in [('alternate-id', 'claims-local'), ('other-id', 'other-realm')]:
            graph = deepcopy(self.graph)
            graph['resources'][resource] = graph['resources'].pop('product-identity')
            for row in graph['resources'].values():
                if row.get('authorityRef') == 'product-identity': row['authorityRef'] = resource
            for environment in graph['environments'].values():
                environment = environment['resources']
                environment[resource] = environment.pop('product-identity')
                environment[resource]['realm'] = realm
            (self.root / model.INPUT).write_text(json.dumps(graph))
            for name, (payload, _) in render.materialize(self.root, graph, TEMPLATE).items():
                target = self.root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
            selected = web_identity.resolve(self.root, 'policies')
            self.assertEqual(str(self.root / 'deploy/keycloak' / resource / (realm + '-realm.json')), selected['realmFile'])
            self.assertTrue(selected['authority'].endswith('/realms/' + realm))
            result = self.persona({'PROGRAMKIT_IDENTITY_REALM_FILE': selected['realmFile'],
                                   'PROGRAMKIT_IDENTITY_AUTHORITY': selected['authority']})
            self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_ambiguous_stale_and_unsupported_selection(self):
        for shell in (None, 'missing'):
            with self.assertRaisesRegex(ValueError, 'PKW104'):
                web_identity.resolve(self.root, shell)
        selected = web_identity.resolve(self.root, 'policies')
        Path(selected['realmFile']).unlink()
        with self.assertRaisesRegex(ValueError, 'PKW103|PKW102'):
            web_identity.resolve(self.root, 'policies')
        with patch.object(render, 'verify_outputs', side_effect=ValueError('PRIVATE_INPUT_SENTINEL')):
            with self.assertRaisesRegex(ValueError, '^PKW103') as error:
                web_identity.resolve(self.root, 'policies')
            self.assertNotIn('PRIVATE_INPUT_SENTINEL', str(error.exception))
        graph = deepcopy(self.graph)
        for environment in graph['environments'].values():
            environment['resources']['product-identity'] = {'provider': 'oidc', 'mode': 'external', 'issuer': 'https://example.test'}
        with patch.object(render, 'verify_outputs', return_value=(graph, {'environment': graph['defaultEnvironment']})):
            with self.assertRaisesRegex(ValueError, 'PKW105'):
                web_identity.resolve(self.root, 'policies')

    def test_persona_requires_both_typed_inputs_and_sanitizes_bad_fixture(self):
        realm = self.root / 'deploy/keycloak/product-identity/program-kit-realm.json'
        for environment in ({}, {'PROGRAMKIT_IDENTITY_REALM_FILE': str(realm)}):
            result = self.persona(environment)
            self.assertNotEqual(0, result.returncode)
            self.assertIn('PKW101', result.stderr)
        realm.write_text('PRIVATE_CREDENTIAL_SENTINEL invalid json')
        result = self.persona({'PROGRAMKIT_IDENTITY_REALM_FILE': str(realm), 'PROGRAMKIT_IDENTITY_AUTHORITY': 'http://localhost/realms/program-kit'})
        self.assertNotEqual(0, result.returncode)
        self.assertIn('PKW102', result.stderr)
        self.assertNotIn('PRIVATE_CREDENTIAL_SENTINEL', result.stderr + result.stdout)

    def test_legacy_fallback_stays_inside_consumer(self):
        (self.root / model.INPUT).unlink()
        self.assertEqual({}, web_identity.resolve(self.root))
        target = self.root / 'deploy/keycloak/program-kit-realm.json'
        shutil.copyfile(self.root / 'deploy/keycloak/product-identity/program-kit-realm.json', target)
        result = self.persona({})
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
