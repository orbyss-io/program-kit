"""Executable selected wire admission; proposals never stand in for producer evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/templates/dotnet/files/eng'))
import openapi_capabilities as admission
sys.path.insert(0, str(ROOT / 'extensions/program-kit-building-blocks/scripts'))
import building_blocks as blocks


class WireCapabilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capabilities = admission.selected(ROOT)
        cls.effective = blocks.effective_dependency_context(ROOT)

    def document(self):
        fields = self.capabilities['problem']['fields']
        document = {'openapi': '3.1.0', 'paths': {'/operations': {'post': {
            'x-foundation-json-contracts': [{'direction': 'request', 'profile': 'strict-request', 'preset': 'strict-request'},
                                          {'direction': 'response', 'profile': 'success-response', 'preset': 'tolerant-response'}],
            'requestBody': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Input'}}}},
            'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/Outcome'}}}},
                          '400': {'content': {'application/problem+json': {'schema': {'$ref': '#/components/schemas/Problem'}}}},
                          '500': {'content': {'application/problem+json': {'schema': {'$ref': '#/components/schemas/Problem'}}}}}}}},
            'components': {'schemas': {
                'Input': {'type': 'object', 'additionalProperties': False, 'properties': {'revision': {'type': 'integer'},
                           'items': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'properties': {'amount': {'type': ['number', 'null']}}}}}},
                'Outcome': {'type': 'object', 'properties': {'operationId': {'type': 'string'}, 'retryMode': {'type': 'string'}, 'statusPath': {'type': 'string'}}},
                'Problem': {'type': 'object', 'properties': {field: {'type': self.capabilities['problem']['fieldTypes'][field]} for field in fields},
                            'additionalProperties': False}}}}
        document['components']['schemas']['Problem']['properties']['fieldErrors']['items'] = {
            'type': 'object', 'additionalProperties': False,
            'properties': {field: {'type': 'string'} for field in self.capabilities['problem']['fieldErrorFields']}}
        return document

    def test_exact_captured_constraints_and_supported_typed_recovery(self):
        self.assertEqual(self.effective['profile'], self.capabilities['profile'])
        self.assertEqual(self.effective['publisherKnowledge']['sourceCommit'], self.capabilities['sourceCommit'])
        capture = self.effective['publisherKnowledge']
        envelope = next(row for row in capture['documents'] if row['publisherPath'] ==
            'src/Orbyss.Foundation.Web.ProblemDetails/FoundationProblemEnvelope.cs')
        source = blocks.publisher_document_bytes(Path(self.effective['registryPath']), envelope).decode('utf-8')
        expected = {'Orbyss.Foundation.Json', 'Orbyss.Foundation.Json.AspNetCore', 'Orbyss.Foundation.Web.ProblemDetails'}
        if 'IReadOnlyList<FoundationProblemFieldError>' not in source:
            expected.add('Orbyss.Foundation.Web.ProblemDetails.Core')
        self.assertEqual(expected, set(self.capabilities['packages']))
        self.assertEqual(['field', 'code', 'message'], self.capabilities['problem']['fieldErrorFields'])
        for package, version in self.capabilities['packages'].items():
            self.assertEqual(self.effective['catalog']['packages']['nuget:' + package]['version'], version, package)
        self.assertEqual({'type', 'title', 'status', 'code', 'correlationId', 'traceId', 'fieldErrors', 'detail'}, set(self.capabilities['problem']['fields']))
        result = admission.require(self.document(), self.capabilities)
        self.assertFalse(result['runtimeEvidence'])
        producer = admission.require(self.document(), self.capabilities, 'producer')
        self.assertTrue(producer['producerDocument'])
        self.assertFalse(producer['runtimeEvidence'])

    def test_custom_problem_fields_rejected_at_exact_pointer(self):
        for field in ('retryMode', 'statusPath', 'instance'):
            document = self.document(); document['components']['schemas']['Problem']['properties'][field] = {'type': 'string'}
            result = admission.validate(document, self.capabilities)
            self.assertFalse(result['admitted'])
            provenance = ('Orbyss.Foundation.Web.ProblemDetails@' + self.capabilities['packages']['Orbyss.Foundation.Web.ProblemDetails']
                          + '; profile=' + self.effective['profile'] + '; source=' + self.effective['publisherKnowledge']['sourceCommit'])
            self.assertTrue(any('#/components/schemas/Problem/properties/' + field in message and provenance in message for message in result['findings']))
        document = self.document(); document['components']['schemas']['Problem'].pop('additionalProperties')
        self.assertTrue(any('additionalProperties' in f for f in admission.validate(document, self.capabilities)['findings']))

    def test_success_only_and_missing_bindings_are_unresolved(self):
        document = self.document(); operation = document['paths']['/operations']['post']
        operation['responses'] = {'200': operation['responses']['200']}
        self.assertTrue(any('success-only' in f for f in admission.validate(document, self.capabilities)['findings']))
        operation['x-foundation-json-contracts'] = []
        self.assertTrue(any('unresolved selected request profile' in f for f in admission.validate(document, self.capabilities)['findings']))

    def test_error_description_optional_detail_and_unknown_members_are_not_proof(self):
        document = self.document(); document['paths']['/operations']['post']['responses']['400'] = {'description': 'Validation failed'}
        self.assertTrue(any('no checked JSON schema' in f for f in admission.validate(document, self.capabilities)['findings']))
        document = self.document(); document['components']['schemas']['Problem']['required'] = ['detail']
        self.assertTrue(any('optional safe detail' in f for f in admission.validate(document, self.capabilities)['findings']))
        document = self.document(); document['components']['schemas']['Input'].pop('additionalProperties')
        self.assertTrue(any('rejects unknown members' in f for f in admission.validate(document, self.capabilities)['findings']))
        result = admission.validate(self.document(), self.capabilities, profiles={'strict-request': {'Extensions': ['owned-converter']}})
        self.assertTrue(any('custom JSON' in f for f in result['findings']))

    def test_nested_nullable_array_numeric_strings_rejected(self):
        document = self.document()
        document['components']['schemas']['Input']['properties']['items']['items']['properties']['amount']['type'] = ['number', 'string', 'null']
        result = admission.validate(document, self.capabilities)
        self.assertTrue(any('/items/items/properties/amount' in f and 'Strict' in f for f in result['findings']))
        nullable = next(f for f in result['findings'] if '/items/items/properties/amount' in f)
        self.assertIn('unresolved nullable numeric producer/profile mismatch', nullable)
        self.assertIn('despite class/property Strict metadata', nullable)
        self.assertIn('retain strict parser, existing annotations and compatibility baseline', nullable)
        self.assertIn('faithful actual metadata/profile proof', nullable)
        self.assertIn('separately supported publisher correction', nullable)
        self.assertNotIn('apply scoped JsonNumberHandling.Strict', nullable)

    def test_nested_problem_promises_and_cross_direction_custom_profiles_unresolved(self):
        document = self.document()
        items = document['components']['schemas']['Problem']['properties']['fieldErrors']['items']
        items['properties']['submittedValue'] = {'type': 'string'}
        self.assertTrue(any('custom nested promises' in f for f in admission.validate(document, self.capabilities)['findings']))
        document = self.document(); operation = document['paths']['/operations']['post']
        operation['responses']['200']['content']['application/json']['schema'] = {'$ref': '#/components/schemas/Input'}
        self.assertTrue(admission.require(document, self.capabilities)['sharedDefaultBindings'])
        operation['x-foundation-json-contracts'][1]['profile'] = 'custom-response'
        result = admission.validate(document, self.capabilities, profiles={'custom-response': {'Preset': 'tolerant-response'}})
        self.assertTrue(any('cross-direction' in f for f in result['findings']))

    def test_malformed_and_recursive_shapes_fail_with_scoped_diagnostics(self):
        documents = [[], {'paths': []}, {'paths': {'/x': []}}, {'paths': {'/x': {'post': []}}}]
        for field, invalid in [('responses', []), ('x-foundation-json-contracts', {}), ('x-foundation-json-contracts', [1])]:
            document = self.document(); document['paths']['/operations']['post'][field] = invalid; documents.append(document)
        for invalid in [False, {'$ref': {}}, {'type': [{}]}, {'properties': []}, {'allOf': {}}, {'required': [1]}]:
            document = self.document(); document['components']['schemas']['Input'] = invalid; documents.append(document)
        document = self.document(); document['components']['schemas']['Input']['properties']['self'] = {'$ref': '#/components/schemas/Input'}; documents.append(document)
        for document in documents:
            with self.subTest(document=document):
                result = admission.validate(document, self.capabilities)
                self.assertFalse(result['admitted'])
                self.assertTrue(any('PKO220 #' in f for f in result['findings']))

    def test_missing_knowledge_shared_profiles_custom_binding_never_assumed(self):
        capabilities = deepcopy(self.capabilities); capabilities['unresolved'].append('selected historical binding missing')
        self.assertFalse(admission.validate(self.document(), capabilities)['admitted'])
        document = self.document(); operation = deepcopy(document['paths']['/operations']['post'])
        operation['x-foundation-json-contracts'][0]['profile'] = 'other-request'
        document['paths']['/other'] = {'post': operation}
        self.assertTrue(any('different profiles' in f for f in admission.validate(document, self.capabilities)['findings']))
        operation['x-foundation-json-contracts'][0]['converters'] = ['owned-converter']
        self.assertTrue(any('custom JSON' in f for f in admission.validate(document, self.capabilities)['findings']))

    def test_no_prose_or_empty_schema_pass(self):
        self.assertFalse(admission.validate({'paths': {}}, self.capabilities)['admitted'])
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as name:
            root = Path(name); (root / 'eng').mkdir()
            (root / 'eng/openapi-contracts.json').write_text(json.dumps({'contracts': []}))
            with self.assertRaisesRegex(ValueError, 'no scoped registered'):
                admission.check_registered(root)

    def test_explicit_registered_wire_check_preserves_history_without_phase_gate(self):
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
        import phase_obligations
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as name:
            root = Path(name); (root / 'eng').mkdir(); feature = root / 'specs/001-api'; feature.mkdir(parents=True)
            (feature / 'plan.md').write_text('Numeric.Contract existing accepted intent; T007 and T012 retained.')
            (root / 'eng/openapi-contracts.json').write_text(json.dumps({'contracts': ['contract.json']}))
            (root / 'contract.json').write_text(json.dumps({'identity': 'numeric', 'features': ['Numeric.Contract'], 'artifact': 'openapi.json', 'shell': 'default'}))
            (root / 'shells.json').write_text(json.dumps({'CShells': {'Shells': {'default': {'Features': {}, 'Configuration': {}}}}}))
            (root / 'baseline.json').write_bytes(b'original immutable compatibility history')
            document = self.document(); document['components']['schemas']['Problem']['properties']['retryMode'] = {'type': 'string'}
            (root / 'openapi.json').write_text(json.dumps(document))
            # Guidance starts no producer validation. The explicitly selected
            # wire operation still rejects the concrete unsupported field.
            with patch.object(admission, 'check_registered', side_effect=AssertionError('Implicit wire check')):
                phase_obligations.check(root, feature, 'after-plan')
            with patch.object(admission, 'selected', return_value=self.capabilities):
                with self.assertRaisesRegex(ValueError, 'Problem/properties/retryMode'):
                    admission.check_registered(root, feature)
            self.assertEqual(b'original immutable compatibility history', (root / 'baseline.json').read_bytes())
            self.assertIn('T007 and T012 retained', (feature / 'plan.md').read_text())

    def test_raw_producer_rejection_precedes_baseline_and_client_writes(self):
        import openapi_pipeline
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as name:
            root = Path(name); raw = root / 'raw.json'
            document = self.document(); document['components']['schemas']['Input']['properties']['revision']['type'] = ['integer', 'string']
            raw.write_text(json.dumps(document))
            shell = root / 'effective-shells.json'; shell.write_text(json.dumps({'CShells': {'Shells': {'default': {'Configuration': {}}}}}))
            paths = {'packages': root / 'stage/packages', 'closureEvidence': root / 'closure.json', 'raw': raw}
            with patch.object(openapi_pipeline.runtime_closure, 'validate'), patch.object(openapi_pipeline, 'run') as producer, \
                 patch.object(admission, 'selected', return_value=self.capabilities), patch.object(openapi_pipeline, 'npm_stage') as client:
                with self.assertRaisesRegex(ValueError, 'PKO222'):
                    openapi_pipeline.execute_contract(root, root / 'contract.json', {'identity': 'numeric', 'shell': 'default'}, paths,
                        None, 'dotnet', root / 'toolchain.json', 'oasdiff', {}, False, False, shell)
                self.assertEqual(1, producer.call_count)
                client.assert_not_called()

    def test_registered_planning_contract_without_runtime_files(self):
        sys.path.insert(0, str(ROOT / 'extensions/program-kit-dotnet/scripts'))
        import composition_model
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as name:
            root = Path(name)
            (root / 'eng').mkdir()
            graph = composition_model.from_legacy(json.loads((ROOT / 'extensions/program-kit-dotnet/templates/dotnet/compositions/foundation-bff-keycloak.json').read_text()))
            (root / 'eng/foundation-composition.json').write_text(json.dumps(graph))
            (root / 'eng/openapi-contracts.json').write_text(json.dumps({'contracts': ['contract.json']}))
            (root / 'contract.json').write_text(json.dumps({'identity': 'catalog', 'features': [], 'artifact': 'proposed.json', 'shell': 'default'}))
            document = self.document()
            (root / 'proposed.json').write_text(json.dumps(document))
            with patch.object(admission, 'selected', return_value=self.capabilities):
                results = admission.check_registered(root, stage='planning')
                self.assertTrue(results[0]['admitted'])
                self.assertFalse(results[0]['runtimeEvidence'])
                with self.assertRaisesRegex(ValueError, 'PKC001'):
                    admission.check_registered(root, stage='producer')
                document['paths'] = {}
                (root / 'proposed.json').write_text(json.dumps(document))
                with self.assertRaisesRegex(ValueError, 'PKO22'):
                    admission.check_registered(root, stage='planning')
            self.assertFalse((root / 'shells.json').exists())


if __name__ == '__main__': unittest.main(verbosity=2)
