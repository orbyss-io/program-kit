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
import composition_render as render
import composition_model as model
from composition_fixture import two_apps


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

    def test_native_browser_declarations_bind_exact_package_files_and_frozen_source(self):
        row = next(row for row in self.effective['publisherKnowledge']['packages'] if row['id'].endswith('.Presentation'))
        path = self.root / row['path']; value = json.loads(path.read_bytes()); value['payloadFiles'] = {}
        documents = []; expected = {}
        for name in ('configuration.d.mts', 'presentation.d.mts', 'bff.d.mts', 'session.d.mts', 'spa.d.mts'):
            data = ('// synthetic package-owned declaration: ' + name + '\n').encode()
            source = self.root / name; source.write_bytes(data); expected[name] = data
            digest = hashlib.sha256(data).hexdigest(); value['payloadFiles']['browser/' + name] = digest
            documents.append({'publisherPath': 'src/Orbyss.Foundation.Web.Presentation/browser/' + name,
                'path': name, 'sha256': digest})
        raw = json.dumps(value).encode(); path.write_bytes(raw)
        row.update(sha256=hashlib.sha256(raw).hexdigest(), byteLength=len(raw))
        self.effective['publisherKnowledge']['documents'] = documents
        native = dependency_profile.resolver()
        resolver = SimpleNamespace(effective_dependency_context=lambda _: self.effective,
            publisher_document_bytes=native.publisher_document_bytes)
        with patch.object(dependency_profile, 'resolver', return_value=resolver):
            self.assertEqual(expected, foundation.browser_declarations(self.root))
            (self.root / 'session.d.mts').write_bytes(b'changed declaration')
            with self.assertRaisesRegex(ValueError, 'differs from its exact native package'):
                foundation.browser_declarations(self.root)
            self.assertEqual(b'changed declaration', (self.root / 'session.d.mts').read_bytes())

    def test_generated_binding_updates_untouched_entry_and_refuses_unreviewed_or_stale_custom_source(self):
        graph = two_apps(ROOT); template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
        frontend = graph['resources']['policy-web']; entry = frontend['directory'] + '/' + frontend['entry']
        original = (template / 'hosted-pages/web/src/app.ts').read_bytes()
        selected = {'settings': {'RoutePrefix': '/account', 'Copy': {'sign-out': 'Leave'}}}
        with patch.object(foundation, 'browser_declarations', return_value={'presentation.d.mts': b'// fixture declaration'}):
            proposed = render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            self.assertIn(b'await bindFoundationPresentation(root)', proposed[entry][0])
            helper = proposed[str(Path(entry).parent).replace('\\', '/') + '/foundation-controls.ts'][0]
            self.assertIn(b'configurationPath = "/account/configuration"', helper)
            self.assertIn(b'textContent = "Leave"', helper)
            current = self.root / entry; current.parent.mkdir(parents=True); current.write_bytes(original)
            digest = hashlib.sha256(original).hexdigest(); manifest = self.root / '.program-kit/managed.json'; manifest.parent.mkdir()
            manifest.write_text(json.dumps({'files': {entry: {'ownership': 'scaffold', 'contribution': 'foundation',
                'sourceIdentity': '../../scripts/foundation_composition.py', 'lastWrittenHash': digest, 'baselineHash': digest}}}))
            render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            custom = original + b'\n// Owned editor and acknowledged draft logic.\n'; current.write_bytes(custom)
            with self.assertRaisesRegex(ValueError, 'custom browser entrypoint requires reconciliation'):
                render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            graph['resources']['application-shell']['presentation'] = {'enabled': True, 'entrypoints': {'policy-web': hashlib.sha256(custom).hexdigest()}}
            reviewed = render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            self.assertEqual(custom, reviewed[entry][0]); self.assertEqual(custom, current.read_bytes())
            current.write_bytes(custom + b'// Later edit\n')
            with self.assertRaisesRegex(ValueError, 'reviewed custom browser entrypoint changed'):
                render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            # The initial source review does not freeze ordinary development
            # after the native managed binding was actually installed.
            helper_path = str(Path(entry).parent).replace('\\', '/') + '/foundation-controls.ts'
            (self.root / helper_path).write_bytes(helper)
            state = json.loads(manifest.read_bytes())
            state['files'][helper_path] = {'ownership': 'managed', 'contribution': 'foundation',
                'sourceIdentity': '../../scripts/foundation_composition.py', 'lastWrittenHash': hashlib.sha256(helper).hexdigest()}
            manifest.write_text(json.dumps(state))
            owned = render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
            self.assertEqual(current.read_bytes(), owned[entry][0])

    def test_frontend_branding_is_independent_of_identity_theme(self):
        graph = two_apps(ROOT); branding = model.default_branding()
        branding.update(theme='green', defaultLocale='en-GB')
        branding['locales']['en-GB']['title'] = 'Owned application'
        graph['resources']['policy-web']['branding'] = branding
        self.assertEqual({'ApplicationName': 'Owned application', 'Locale': 'en-GB', 'Theme': 'green'},
            render.presentation_branding(graph, 'application-shell'))

    def test_nested_shell_binding_uses_the_effective_native_configuration_route(self):
        graph = two_apps(ROOT); graph['resources']['application-shell']['pathBase'] = '/products/orders'
        template = ROOT / 'extensions/program-kit-dotnet/templates/dotnet'
        frontend = graph['resources']['policy-web']; entry = frontend['directory'] + '/' + frontend['entry']
        original = (template / 'hosted-pages/web/src/app.ts').read_bytes()
        selected = {'settings': {'RoutePrefix': '/account', 'Copy': {}}}
        with patch.object(foundation, 'browser_declarations', return_value={}):
            files = render.presentation_frontend(self.root, graph, 'policy-web', selected, template, {entry: (original, 'scaffold')})
        helper = files[(Path(entry).parent / 'foundation-controls.ts').as_posix()][0]
        self.assertIn(b'configurationPath = "/products/orders/account/configuration"', helper)

    def test_custom_entrypoint_review_cannot_bind_a_foreign_frontend(self):
        graph = two_apps(ROOT)
        graph['resources']['application-shell']['presentation'] = {'enabled': True, 'entrypoints': {'assessment-web': 'a' * 64}}
        with self.assertRaisesRegex(ValueError, 'frontend bound to this shell'): model.validate(graph)


if __name__ == '__main__': unittest.main()
