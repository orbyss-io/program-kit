"""Native profile projection guards; synthetic facts establish no publisher qualification."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
import dependency_profile
import foundation_composition as foundation
import spa_profile


class PresentationProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='presentation-profile-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        self.effective = {'registryPath': str(self.root), 'profile': 'synthetic-only', 'profileEntrySha256': 'a' * 64,
            'publisherKnowledge': {'hostImage': {}, 'packages': []}, 'catalog': {'packages': {}}}
        self.package('Orbyss.Foundation.WebDefaults', {'SessionIdleMinutes': 30, 'SessionAbsoluteMinutes': 480}, 'Foundation:Web:')
        self.package('Orbyss.Foundation.Web.Presentation', {'ApplicationName': 'Native default', 'Locale': 'en', 'Theme': 'blue',
            'RoutePrefix': '/auth', 'ReturnPath': '/', 'ResponsePolicy': 'private', 'AssetResponsePolicy': 'public-asset',
            'SignOutConfirmation': 'when-unsaved', 'Copy': {}}, 'Foundation:Web:Presentation:')

    def package(self, identity, defaults, prefix):
        settings = [{'path': prefix + key, 'default': value,
            'type': 'string' if isinstance(value, str) else 'object' if isinstance(value, dict) else 'integer',
            'constraints': {'enum': ['blue', 'green', 'slate']} if key == 'Theme' else {}}
            for key, value in defaults.items()]
        facts = {'orbyss-foundation/feature.json': json.dumps({'features': [{'identity': identity,
            'featureDependencies': ['Orbyss.Foundation.WebDefaults'] if identity.endswith('.Presentation') else []}]}),
            'orbyss-foundation/settings.json': json.dumps({'contracts': [{'settings': settings}]})}
        raw = json.dumps({'facts': facts}).encode(); name = identity + '.json'; (self.root / name).write_bytes(raw)
        self.effective['publisherKnowledge']['packages'].append({'id': identity, 'path': name, 'byteOffset': 0,
            'byteLength': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'version': '0.0.0-fixture'})
        self.effective['catalog']['packages']['nuget:' + identity] = {'version': '0.0.0-fixture'}

    def selected(self, presentation=None):
        native = dependency_profile.resolver()
        resolver = SimpleNamespace(effective_dependency_context=lambda _: self.effective,
            publisher_document_bytes=native.publisher_document_bytes)
        with patch.object(dependency_profile, 'resolver', return_value=resolver):
            return foundation.publisher_contracts(self.root, selected_packages=['Orbyss.Foundation.WebDefaults'], presentation=presentation)

    def test_native_metadata_defaults_and_selected_theme_bind_the_actual_landing_path(self):
        selected = self.selected({'enabled': True, 'settings': {'ApplicationName': 'Owned', 'Theme': 'green', 'RoutePrefix': '/account'}})
        self.assertIn('Orbyss.Foundation.Web.Presentation', selected['activations'])
        self.assertEqual('green', selected['browserPresentation']['settings']['Theme'])
        configuration = {'settings': {}, 'application': {'callbackPath': '/signin-oidc', 'signedOutCallbackPath': '/signout-callback-oidc', 'localDevelopment': True},
            'identity': {'publicOrigin': 'http://localhost:8080', 'backchannelOrigin': 'http://identity:8080',
                'realm': 'fixture', 'clientId': 'fixture', 'audience': 'fixture'}}
        web = foundation.web_settings(configuration, selected)
        self.assertEqual('/account/signed-out', web['LogoutLandingPath'])
        self.assertEqual('Owned', web['Presentation']['ApplicationName'])

    def test_independent_disable_removes_only_the_presentation_activation(self):
        selected = self.selected({'enabled': False})
        self.assertEqual(['Orbyss.Foundation.WebDefaults'], selected['activations'])
        self.assertNotIn('Orbyss.Foundation.Web.Presentation', selected['packages'])
        self.assertEqual({'enabled': False}, selected['browserPresentation'])

    def test_bad_public_option_type_or_theme_and_missing_published_capability_reject(self):
        for settings in ({'Theme': 'arbitrary-css'}, {'ApplicationName': 7}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.selected({'enabled': True, 'settings': settings})
        self.effective['publisherKnowledge']['packages'] = self.effective['publisherKnowledge']['packages'][:1]
        self.effective['catalog']['packages'].pop('nuget:Orbyss.Foundation.Web.Presentation')
        self.assertNotIn('browserPresentation', self.selected())
        with self.assertRaisesRegex(ValueError, 'published qualified'):
            self.selected({'enabled': True})

    def test_spa_redirect_and_popup_have_distinct_matching_contract_and_vite_policies(self):
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet/web-profiles/spa-pkce/eng'
        configuration = json.loads((template / 'spa-pkce.json').read_bytes())
        original = copy.deepcopy(configuration)
        for mode, expected in (('redirect', 'same-origin'), ('popup', 'same-origin-allow-popups')):
            configuration['authenticationNavigation'] = mode
            spa_profile.validate_configuration(configuration)
            security = json.loads(spa_profile.render_security_contract((template / 'web/spa-security.json').read_bytes(), configuration))
            source = spa_profile.render_vite_security((template / 'web/vite.security.mjs').read_bytes(), configuration).decode()
            self.assertEqual(expected, security['headers']['Cross-Origin-Opener-Policy'])
            self.assertIn("'Cross-Origin-Opener-Policy': '" + expected + "'", source)
            self.assertEqual(original['redirectUris'], configuration['redirectUris'])
        configuration['authenticationNavigation'] = 'unsafe-none'
        with self.assertRaisesRegex(ValueError, 'PKW113'): spa_profile.validate_configuration(configuration)


if __name__ == '__main__': unittest.main()
