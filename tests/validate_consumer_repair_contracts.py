"""Synthetic offline repair regressions. No private consumer data or agent dispatch."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'extensions/program-kit-governance/scripts'),
               str(ROOT / 'extensions/program-kit-dotnet/scripts'), str(ROOT / 'tests')]
import bootstrap_lifecycle as lifecycle
import phase_obligations as phases
import composition_model as model
import composition_render as renderer
import composition_fixture
import repository_architecture
import shell_composition


class RepairContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='synthetic-repairs-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def write(self, name, value):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value), encoding='utf-8')
        return p

    def test_promotion_preserves_executed_bytes_but_not_changed_pins(self):
        selection = self.write('docs/architecture/building-block-selection.json',
                               {'status': 'Draft', 'instances': [{'package': 'Example.Catalog', 'version': '1.0'}]})
        profile = self.write('.program-kit/dependency-profile.json', {
            'authority': 'retained Draft dependency suggestions; no acceptance or compatibility approval', 'profile': 'example-v1'})
        originals = {p: p.read_bytes() for p in (selection, profile)}
        attempt = self.root / 'attempt'; attempt.mkdir()
        records = []
        inputs = lifecycle.capture_lifecycle_inputs(self.root, attempt,
            [{'path': p.relative_to(self.root).as_posix(), 'sha256': lifecycle.digest(p)} for p in originals], records)
        proof = {'inputs': inputs, 'lifecycle_inputs': records}
        receipt = attempt / 'proof.json'
        selected = json.loads(selection.read_text()); selected['status'] = 'Accepted'
        selection.write_text(json.dumps(selected))
        accepted = json.loads(profile.read_text()); accepted['authority'] = 'retained accepted selection; no new compatibility claim'
        profile.write_text(json.dumps(accepted))
        self.assertTrue(lifecycle.lifecycle_inputs_current(self.root, proof, receipt))
        self.assertEqual(originals[selection], (attempt / 'executed-inputs/building-block-selection.json').read_bytes())
        selected['instances'][0]['version'] = '2.0'; selection.write_text(json.dumps(selected))
        self.assertFalse(lifecycle.lifecycle_inputs_current(self.root, proof, receipt))
        for mutation in ('missing', 'duplicate', 'outside', 'semantic', 'bytes'):
            candidate = deepcopy(proof)
            if mutation == 'missing': candidate['lifecycle_inputs'] = []
            elif mutation == 'duplicate': candidate['lifecycle_inputs'].append(candidate['lifecycle_inputs'][0])
            elif mutation == 'outside': candidate['lifecycle_inputs'][0]['snapshotPath'] = 'elsewhere.json'
            elif mutation == 'semantic': candidate['lifecycle_inputs'][0]['semanticSha256'] = '0' * 64
            else: candidate['inputs'][0]['sha256'] = '0' * 64
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                lifecycle.lifecycle_inputs_current(self.root, candidate, receipt)
        self.assertTrue(lifecycle.lifecycle_inputs_current(self.root, {'inputs': []}, receipt))

    def test_native_cwd_limit_is_independent_of_extended_file_paths(self):
        lifecycle.require_native_scratch(Path('C:/trials/example'), platform='nt')
        with self.assertRaisesRegex(ValueError, 'PKL024'):
            lifecycle.require_native_scratch(Path('C:/' + 'x' * 240), platform='nt')
        lifecycle.require_native_scratch(Path('/' + 'x' * 270), platform='posix')

    def test_transport_pages_preserve_unicode_and_every_duty(self):
        content = ('Catalog constraints café 中文\n' * 1500) + 'FINAL MANDATORY RULE'
        pages = []
        for number in range(1, 100):
            try: page = phases.text_page(content, number)
            except ValueError: break
            self.assertLessEqual(len(page.encode('utf-8')), 10500)
            pages.append(page.split('\n', 1)[1])
        self.assertEqual(content, ''.join(pages))
        with self.assertRaisesRegex(ValueError, 'PKC026'): phases.text_page(content, 0)

    def test_scoped_core_identity_and_package_names(self):
        path = 'src/Example.CatalogModel/Example.CatalogModel.csproj'
        row = {'path': path, 'role': 'core', 'projectReferences': [], 'packageReferences': [],
               'responsibilities': [{'name': 'CatalogMeaning', 'kind': 'contract', 'effects': [], 'provides': []}]}
        manifest = {'runtimeComposition': {'projects': [row], 'bindings': []}}
        repository_architecture.validate_planned(self.root, manifest)  # retained unrelated graph
        with self.assertRaisesRegex(ValueError, 'PKA023'):
            repository_architecture.validate_planned(self.root, manifest, require_responsibilities=True)
        row['path'] = 'src/Example.Catalog.Core/Example.Catalog.Core.csproj'
        repository_architecture.validate_planned(self.root, manifest, require_responsibilities=True)
        row['packageId'] = 'Different.Identity'
        with self.assertRaisesRegex(ValueError, 'project/package'):
            repository_architecture.validate_planned(self.root, manifest, require_responsibilities=True)
        row.pop('packageId')
        row['path'] = 'src/Example.Feature.Core/Example.Feature.Core.csproj'
        with self.assertRaisesRegex(ValueError, 'generic .Feature'):
            repository_architecture.validate_planned(self.root, manifest, require_responsibilities=True)

    def graph(self):
        return model.from_legacy(json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak-postgresql.json').read_text()))

    def test_selected_publishers_retain_native_versions_and_activations(self):
        graph = self.graph()
        selection, _ = composition_fixture.accept_fixture(self.root, graph, ROOT)
        value = json.loads(selection.read_text())
        api = next(t['id'] for t in value['targets'] if t['kind'] == 'dotnet-project' and t['role'] == 'implementation')
        for identity, composition in [('locale', 'localization_runtime'), ('forms', 'forms_management')]:
            value['instances'].append({'id': identity, 'composition': composition, 'scope': 'application',
                                      'targetBindings': {'dotnet': api, 'shell': 'application-shell'}, 'options': {}})
        selection.write_text(json.dumps(value))
        path = self.root / 'docs/architecture/architecture-map.json'
        architecture = json.loads(path.read_text()); architecture['documentation'][0]['sha256'] = hashlib.sha256(selection.read_bytes()).hexdigest()
        path.write_text(json.dumps(architecture))
        files = renderer.materialize(self.root, graph, ROOT / 'extensions/program-kit-dotnet/templates/dotnet')
        contract = json.loads(files['eng/foundation-settings.contract.json'][0])
        shell = contract['shells']['application-shell']
        self.assertEqual('0.1.2', shell['packages']['Orbyss.Localization.Runtime'])
        self.assertEqual('0.2.1', shell['packages']['Orbyss.Forms.Management'])
        self.assertIn('Orbyss.Localization.Web.Runtime', shell['activations'])
        self.assertIn('Orbyss.Forms.Management', shell['activations'])
        api_source = next(data[0].decode() for name, data in files.items() if name.endswith('/ApiFeature.cs'))
        self.assertIn('"Orbyss.Localization.Runtime"', api_source)
        self.assertIn('"Orbyss.Forms.Management"', api_source)
        admitted = renderer.accepted_selection(self.root)
        admitted['targets'] = []
        with self.assertRaisesRegex(ValueError, 'native package binding'):
            renderer.selected_publisher_activations(graph, 'application-shell', admitted)

    def test_planning_shell_uses_typed_proposal_and_retains_runtime_gate(self):
        graph = self.graph()
        self.write('eng/foundation-composition.json', graph)
        projected = shell_composition.compose(self.root, planning=True)
        self.assertIn('default', projected['CShells']['Shells'])
        self.assertFalse((self.root / 'shells.json').exists())
        with self.assertRaisesRegex(ValueError, 'PKC001'): shell_composition.compose(self.root)
        self.write('shells.json', {'CShells': {'Shells': {'other': {'Features': {}}}}})
        with self.assertRaisesRegex(ValueError, 'PKC007'): shell_composition.compose(self.root, planning=True)
        (self.root / 'shells.json').unlink()
        (self.root / 'eng/foundation-composition.json').unlink()
        with self.assertRaisesRegex(ValueError, 'PKC001'): shell_composition.compose(self.root, planning=True)

    def test_planning_preserves_multiple_named_shells_in_one_declared_source(self):
        graph = composition_fixture.two_apps(ROOT, frontends=False)
        for row in model.resources(graph, 'shell').values():
            row['source'] = 'runtime/shared/shells.json'
        self.write('eng/foundation-composition.json', graph)
        projected = shell_composition.compose(self.root, planning=True)
        self.assertEqual({row['name'] for row in model.resources(graph, 'shell').values()},
                         set(projected['CShells']['Shells']))
        self.assertFalse((self.root / 'runtime/shared/shells.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
