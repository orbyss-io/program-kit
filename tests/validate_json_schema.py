"""Offline behavior tests for shipped JSON Schema tools and independent installations."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'extensions/program-kit-governance/scripts'
sys.path.insert(0, str(SCRIPTS))
import json_schema as tool
import schema_runtime as runtime


class SchemaTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='program-kit-schema-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.schema = {'$schema': tool.DRAFTS[-1], 'type': 'object'}

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return path

    def cli(self, schema, value, *args):
        schema_path = self.write('schema.json', schema)
        input_path = self.write('input.json', value)
        before = (schema_path.read_bytes(), input_path.read_bytes())
        result = subprocess.run([sys.executable, str(SCRIPTS / 'json_schema.py'), 'validate',
                                 '--schema', str(schema_path), '--input', str(input_path), *args],
                                capture_output=True, encoding='utf-8', timeout=30)
        self.assertEqual(before, (schema_path.read_bytes(), input_path.read_bytes()))
        return result.returncode, json.loads(result.stdout)

    def test_dialects_and_integral_float(self):
        for dialect in tool.DRAFTS:
            schema = {'$schema': dialect, 'type': 'integer'}
            self.assertTrue(tool.validate_value(2.0, schema)['valid'])
            self.assertFalse(tool.validate_value(True, schema)['valid'])

    def test_composition_conditional_and_unevaluated_properties(self):
        schema = dict(self.schema, allOf=[{'properties': {'enabled': {'type': 'boolean'}}}],
                      **{'if': {'properties': {'enabled': {'const': True}}},
                         'then': {'required': ['name'], 'properties': {'name': {'type': 'string'}}},
                         'unevaluatedProperties': False})
        self.assertTrue(tool.validate_value({'enabled': True, 'name': 'café 中文'}, schema)['valid'])
        self.assertFalse(tool.validate_value({'enabled': True}, schema)['valid'])
        self.assertFalse(tool.validate_value({'enabled': False, 'extra': 1}, schema)['valid'])

    def test_batch_paths_limit_and_exit_codes(self):
        schema = dict(self.schema, properties={'a/b': {'type': 'integer'}, 'x': {'enum': ['ok']}}, required=['missing'])
        code, report = self.cli(schema, {'a/b': 'wrong', 'x': 'no'}, '--max-errors', '1')
        self.assertEqual(code, 1)
        self.assertEqual(report['errorCount'], 3)
        self.assertTrue(report['truncated'])
        self.assertEqual(report['errors'][0]['instancePath'], '/a~1b')
        self.assertEqual(self.cli(self.schema, {})[0], 0)
        self.assertEqual(self.cli({'$schema': 'https://unknown.invalid'}, {})[0], 2)
        self.assertEqual(self.cli(dict(self.schema, type=12), {})[0], 2)

    def test_duplicate_keys_nonfinite_and_malformed_json(self):
        for text in ('{"x":1,"x":2}', 'NaN', 'Infinity', '{'):
            path = self.root / 'bad.json'
            path.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                tool.load(path)

    def test_local_and_explicit_logical_references(self):
        child = self.write('child.json', {'$schema': tool.DRAFTS[-1], 'type': 'string'})
        schema = {'$schema': tool.DRAFTS[-1], '$ref': 'child.json'}
        location = self.write('schema.json', schema)
        self.assertTrue(tool.validate_value('yes', schema, location)['valid'])
        logical = {'$schema': tool.DRAFTS[-1], '$id': 'https://example.invalid/child', 'type': 'string'}
        child = self.write('child.json', logical)
        schema['$ref'] = logical['$id']
        self.assertTrue(tool.validate_value('yes', schema, location, [child])['valid'])

    def test_no_network_and_no_implicit_path_escape(self):
        for ref in ('https://example.invalid/schema', '../outside.json'):
            schema = {'$schema': tool.DRAFTS[-1], '$ref': ref}
            with patch('socket.socket', side_effect=AssertionError('network attempted')):
                with self.assertRaises(Exception) as error:
                    tool.validate_value({}, schema, self.root / 'nested/schema.json')
                self.assertNotIsInstance(error.exception, AssertionError)

    def test_recursive_reference_and_description(self):
        schema = dict(self.schema, **{'$defs': {'node': {'type': 'object', 'properties': {
            'next': {'$ref': '#/$defs/node'}, 'label': {'type': 'string'}}}}, '$ref': '#/$defs/node'})
        self.assertTrue(tool.validate_value({'label': 'é', 'next': {'label': '中文'}}, schema)['valid'])
        result = tool.describe_value(schema, '/$defs/node')
        self.assertLess(len(json.dumps(result)), 3000)
        self.assertIn('$ref', json.dumps(result))

    def test_boolean_schema_and_format_policy(self):
        self.assertTrue(tool.validate_value('anything', True)['valid'])
        self.assertFalse(tool.validate_value({}, False)['valid'])
        report = tool.validate_value('not-an-email', {'$schema': tool.DRAFTS[-1], 'format': 'email'})
        self.assertTrue(report['valid'])
        self.assertEqual(report['formatPolicy'], 'annotation-only')

    def test_description_preserves_data_and_nested_reference_scope(self):
        schema = dict(self.schema, **{'$id': 'https://example.invalid/root', '$defs': {
            'nested': {'$id': 'nested', '$defs': {'text': {'type': 'string'}},
                       'properties': {'text': {'$ref': '#/$defs/text'}},
                       'const': {'$ref': 'https://not-a-schema.invalid'}}}})
        value = tool.describe_value(schema, '/$defs/nested')['schema']
        self.assertEqual(value['properties']['text']['type'], 'string')
        self.assertEqual(value['const']['$ref'], 'https://not-a-schema.invalid')
        schema = {'$schema': tool.DRAFTS[0], 'definitions': {'text': {'type': 'string'}},
                  '$ref': '#/definitions/text', 'type': 'integer'}
        self.assertEqual(tool.describe_value(schema)['schema'], {'type': 'string'})

    def test_installed_copy_offline_and_edit_guard(self):
        installed = self.root / runtime.EXTENSION
        installed.mkdir(parents=True)
        for name in runtime.FILES:
            shutil.copy2(SCRIPTS / name, installed / name)
        cached = runtime.runtime_path(self.root)
        cached.parent.mkdir(parents=True)
        shutil.copytree(runtime.runtime_path(), cached)
        with self.assertRaisesRegex(RuntimeError, 'BASELINE_MISSING'):
            runtime.check_copy(self.root)
        runtime.record_copy(self.root)
        runtime.check_copy(self.root)
        schema = self.write('schema.json', self.schema)
        data = self.write('input.json', {})
        result = subprocess.run([sys.executable, str(installed / 'json_schema.py'), 'validate',
                                 '--schema', str(schema), '--input', str(data)], capture_output=True,
                                encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source_before = (SCRIPTS / 'json_schema.py').read_bytes()
        with (installed / 'json_schema.py').open('a', encoding='utf-8') as stream:
            stream.write('\n# Deliberate consumer modification\n')
        self.assertEqual(source_before, (SCRIPTS / 'json_schema.py').read_bytes())
        with self.assertRaisesRegex(RuntimeError, 'LOCALLY_EDITED'):
            runtime.check_copy(self.root)

    def test_setup_is_explicit_and_offline_reuses_existing_runtime(self):
        with patch.object(runtime.subprocess, 'run', side_effect=AssertionError('unexpected installer')):
            self.assertEqual(runtime.setup(offline=True), runtime.runtime_path())
            tool.validate_value({}, self.schema)
            with self.assertRaisesRegex(RuntimeError, 'SCHEMA_RUNTIME_MISSING'):
                runtime.setup(self.root, offline=True)

    def test_nested_unsupported_dialect_is_not_silently_accepted(self):
        schema = dict(self.schema, properties={'x': {'$schema': 'https://unknown.invalid', 'type': 'string'}})
        with self.assertRaises(Exception):
            tool.validate_value({'x': 'ok'}, schema)


if __name__ == '__main__':
    unittest.main()
