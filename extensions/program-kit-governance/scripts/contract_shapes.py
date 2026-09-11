"""Intake compatibility adapter over the reusable JSON Schema engine."""
import json
from pathlib import Path
from json_schema import validate_value, describe_value

REFERENCES = Path(__file__).resolve().parent.parent / 'references'


def schema_for(document):
    name = {'map': 'architecture-map', 'intake': 'bootstrap-intake'}[document]
    return json.loads((REFERENCES / f'{name}.schema.json').read_text(encoding='utf-8'))


def errors(value, schema, root=None, path='$'):
    if root is not None and root is not schema:
        raise ValueError('Validate complete documents, not detached subschemas.')
    report = validate_value(value, schema)
    return [f'{path}{item["instancePath"]}: {item["message"]}' for item in report['errors']]


def describe(document, section):
    schema = schema_for(document)
    if section == 'root':
        selected = ''
    elif section in schema.get('$defs', {}):
        selected = '/$defs/' + section
    else:
        selected = '/properties/' + section
        if schema['properties'][section].get('type') == 'array':
            selected += '/items'
    value = describe_value(schema, selected)['schema']
    return {'required': value.get('required', []), 'fields': value.get('properties', {})}
