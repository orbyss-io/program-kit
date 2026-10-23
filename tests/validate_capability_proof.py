"""Missing runtime/adoption proof must fail even with a plausible architecture plan."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
from architecture_proof import validate
from capability_adoption import validate_adoption, MECHANISMS
from validate_governance_state import roadmap


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='capability-proof-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.feature = self.root / 'specs/001-equipment'
        self.feature.mkdir(parents=True)
        self.write(self.feature / 'artifact-ownership.json', {'runtimeComposition': {
            'bindings': [{'capability': 'Equipment.IReservations', 'implementationProject': 'src/Reservations/Reservations.csproj'}],
            'coreReferences': []}})
        self.proof = {'schemaVersion': 1, 'graph': {'method': 'evaluated-compiled', 'rationale': 'Inspect imported references and compiled types', 'checkIds': ['graph']},
                      'bindings': [{'id': 'Equipment.IReservations@src/Reservations/Reservations.csproj', 'shell': 'equipment',
                                    'registration': 'ReservationsFeature.ConfigureServices', 'resolutionCheckIds': ['resolve'],
                                    'extensionCheckIds': ['substitute'], 'contract': 'Replacements preserve durable reservation identity and denied-effect behavior'}],
                      'coreReferences': {}}
        self.write(self.feature / 'architecture-proof.json', self.proof)
        (self.feature / 'spec.md').write_text('- **Specification roadmap entry**: SPEC-001\n', encoding='utf-8')
        self.write(self.root / 'docs/architecture/building-block-selection.json', {'instances': [{'id': 'forms', 'composition': 'forms_immutable_release'}]})
        self.adoption = {'instances': [{'id': 'forms', 'owner': 'Equipment team', 'rationale': 'Publish fixed form at build time',
                         'disposition': 'current-feature', 'mechanisms': {m: {'publicApi': 'Released Forms public API',
                         'placement': 'build producer and browser runtime', 'implementationPaths': ['src/forms.ts'], 'checkIds': ['forms']}
                         for m in MECHANISMS['forms_immutable_release']}}]}
        self.write(self.feature / 'capability-adoption.json', self.adoption)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def test_complete_named_architecture_proof(self):
        validate(self.root, self.feature, {'graph', 'resolve', 'substitute'})

    def test_declared_registration_without_runtime_case_is_rejected(self):
        self.proof['bindings'][0]['resolutionCheckIds'] = []
        self.write(self.feature / 'architecture-proof.json', self.proof)
        with self.assertRaisesRegex(ValueError, 'registration/resolution|resolutionCheckIds'):
            validate(self.root, self.feature, {'graph', 'resolve', 'substitute'})

    def test_binding_cannot_omit_extension_compatibility(self):
        with self.assertRaisesRegex(ValueError, 'extension/replacement'):
            validate(self.root, self.feature, {'graph', 'resolve'})

    def test_simple_graph_does_not_invent_extension_points(self):
        self.write(self.feature / 'artifact-ownership.json', {'runtimeComposition': {'bindings': [], 'coreReferences': []}})
        self.proof['bindings'] = []
        self.write(self.feature / 'architecture-proof.json', self.proof)
        validate(self.root, self.feature, {'graph'})

    def test_selected_forms_requires_public_producer_and_renderer(self):
        validate_adoption(self.root, self.feature, 'after-plan', {'forms'})
        self.adoption['instances'][0]['mechanisms'].pop('public-release-production')
        self.write(self.feature / 'capability-adoption.json', self.adoption)
        with self.assertRaisesRegex(ValueError, 'Missing actual mechanism'):
            validate_adoption(self.root, self.feature, 'after-plan', {'forms'})

    def test_future_capability_has_real_other_open_roadmap_owner(self):
        record = self.adoption['instances'][0]
        record.update(disposition='future-feature', roadmapEntry='SPEC-002', duePhase='implementation', authority='docs/architecture/specification-roadmap.md')
        self.write(self.feature / 'capability-adoption.json', self.adoption)
        path = self.root / record['authority']
        path.write_text(roadmap(status='Candidate').replace('SPEC-001', 'SPEC-002'), encoding='utf-8')
        validate_adoption(self.root, self.feature, 'after-plan', set())
        path.write_text(roadmap(status='Delivered').replace('SPEC-001', 'SPEC-002'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'open declared roadmap'):
            validate_adoption(self.root, self.feature, 'after-plan', set())

    def same_epic_future(self):
        brief = '.program-kit/specification-intake/features/policy-terms/brief.json'
        self.write(self.root / brief, {'schemaVersion': 2, 'roadmapEntry': 'SPEC-001', 'featureId': 'policy-terms'})
        (self.feature / 'spec.md').write_text('- **Specification roadmap entry**: SPEC-001\n'
            '- **Specification feature ID**: policy-terms\n- **Confirmed intake brief**: ' + brief + '\n', encoding='utf-8')
        record = self.adoption['instances'][0]
        record.update(disposition='future-feature', roadmapEntry='SPEC-001', featureId='renew-policy',
                      duePhase='implementation', authority='docs/architecture/specification-roadmap.md')
        self.write(self.feature / 'capability-adoption.json', self.adoption)
        path = self.root / record['authority']
        path.write_text(roadmap(status='Candidate'), encoding='utf-8')
        self.write(self.root / 'docs/architecture/architecture-map.json', {'strategic_model': {
            'candidate_slices': [{'id': 'policy-terms', 'epic': 'SPEC-001'}, {'id': 'renew-policy', 'epic': 'SPEC-001'}]}})
        return record

    def test_future_capability_can_belong_to_exact_sibling_in_same_epic(self):
        record = self.same_epic_future()
        validate_adoption(self.root, self.feature, 'after-plan', set())
        # A durable v2 intake also supplies exact parent authority when a seed was
        # introduced by later feature discovery rather than bootstrap.
        (self.root / 'docs/architecture/architecture-map.json').unlink()
        self.write(self.root / '.program-kit/specification-intake/features/renew-policy/brief.json',
                   {'schemaVersion': 2, 'roadmapEntry': 'SPEC-001', 'featureId': 'renew-policy'})
        validate_adoption(self.root, self.feature, 'after-plan', set())

    def test_same_epic_deferral_rejects_self_ambiguity_unknown_and_wrong_parent(self):
        record = self.same_epic_future()
        original = copy.deepcopy(record)
        preserved = (self.feature / 'spec.md').read_bytes()
        for field, value, expected in [('featureId', 'policy-terms', 'same feature'),
                                        ('featureId', None, 'exact target featureId'),
                                        ('featureId', 'unknown-feature', 'parent authority'),
                                        ('roadmapEntry', 'SPEC-002', 'different parent epic')]:
            with self.subTest(field=field, value=value):
                record.clear()
                record.update(original)
                if value is None:
                    record.pop(field)
                else:
                    record[field] = value
                self.write(self.feature / 'capability-adoption.json', self.adoption)
                with self.assertRaisesRegex(ValueError, expected):
                    validate_adoption(self.root, self.feature, 'after-plan', set())
        self.assertEqual(preserved, (self.feature / 'spec.md').read_bytes())


if __name__ == '__main__':
    unittest.main()
