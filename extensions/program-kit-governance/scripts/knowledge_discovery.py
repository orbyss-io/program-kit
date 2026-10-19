"""One discovery entry point for canonical owners, routes and honest proof scope.

Maintainer traversal is explicit, never part of every task projection. The views
are regenerable; consumers do not maintain another knowledge inventory.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
from pathlib import Path
import subprocess
import re
import xml.etree.ElementTree as ET

from knowledge_sources import confined, resolve, effective_rule, marked


CATALOG = Path(__file__).resolve().parents[1] / 'references/phase-obligations.json'


def load():
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def applicable(rule, requirements):
    return bool(set(rule['requirements']) & set(requirements))


def selected(catalog, requirements):
    unknown = set(requirements) - {row['id'] for row in catalog['requirements']}
    if unknown:
        raise ValueError('Unknown responsibility selection: ' + ', '.join(sorted(unknown)))
    return [identity for identity, rule in catalog['rules'].items()
            if rule['status'] == 'active' and applicable(rule, requirements)]


def inspect_declarations(path):
    """Find attributable candidates, never infer authority from a keyword.

    No supplied code executes and no literal/error/private value is printed.
    Diagnostics and examples can look normative: the view labels this limitation.
    """
    if path.suffix.lower() not in ('.py', '.cs', '.json', '.props', '.targets', '.md', '.yml', '.yaml') and path.name != '.editorconfig':
        return {'status': 'non-text-or-other-mechanism', 'candidates': []}
    if path.stat().st_size > 1_048_576:
        return {'status': 'bounded-out; inspect-through-owning-native-reader', 'candidates': []}
    content = path.read_text(encoding='utf-8-sig')
    candidates = []
    if path.suffix == '.py':
        class Candidates(ast.NodeVisitor):
            def __init__(self):
                self.owner = []

            def visit_FunctionDef(self, node):
                self.owner.append(node.name)
                self.generic_visit(node)
                self.owner.pop()

            visit_AsyncFunctionDef = visit_FunctionDef
            visit_ClassDef = visit_FunctionDef

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        candidates.append({'kind': 'named-table-or-constant', 'symbol': '.'.join([*self.owner, target.id]), 'line': node.lineno})
                self.generic_visit(node)

            def visit_Constant(self, node):
                if isinstance(node.value, str) and re.search(r'\b(must|never|forbidden|required|shall)\b|do not', node.value, re.I):
                    candidates.append({'kind': 'policy-like-literal-or-diagnostic', 'symbol': '.'.join(self.owner) or '<module>', 'line': node.lineno})
        Candidates().visit(ast.parse(content))
    elif path.suffix == '.json':
        def walk(value, pointer=''):
            if isinstance(value, dict):
                for key, child in value.items():
                    location = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
                    if key in ('required', 'enum', 'const', 'minimum', 'maximum', 'additionalProperties', 'pattern', '$ref'):
                        candidates.append({'kind': 'native-schema-declaration', 'pointer': location})
                    walk(child, location)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, pointer + '/' + str(index))
        walk(json.loads(content))
    elif path.suffix in ('.props', '.targets'):
        for node in ET.fromstring(content).iter():
            if node.tag.rsplit('}', 1)[-1] in ('PropertyGroup', 'ItemGroup'):
                candidates.extend({'kind': 'native-build-declaration', 'element': child.tag.rsplit('}', 1)[-1],
                                   'conditional': bool(node.get('Condition') or child.get('Condition'))} for child in node)
    else:
        current = None
        for index, line in enumerate(content.splitlines(), 1):
            if path.name == '.editorconfig':
                if line.startswith('['):
                    current = line.strip()
                if '=' in line and not line.lstrip().startswith(('#', ';')):
                    candidates.append({'kind': 'native-editorconfig-declaration', 'section': current,
                                       'key': line.partition('=')[0].strip(), 'line': index})
            elif path.suffix == '.cs' and re.search(r'\b(class|interface|enum|record)\s+\w+|DiagnosticDescriptor', line):
                candidates.append({'kind': 'csharp-contract-or-policy-declaration', 'line': index})
            elif re.search(r'\b(must|never|forbidden|required|shall)\b|do not', line, re.I):
                candidates.append({'kind': 'policy-like-prose-or-diagnostic', 'line': index})
    return {'status': 'inspected-declarations', 'candidates': candidates,
            'limits': 'Candidates require owner review; keywords, examples and diagnostic strings are not automatically normative rules.'}


def discover(repository, catalog):
    result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            cwd=repository, capture_output=True, timeout=20)
    if result.returncode:
        raise ValueError('Knowledge discovery requires the actual tracked tree; Git enumeration failed')
    paths = sorted(set(result.stdout.decode('utf-8').split('\0')) - {''})
    exact = {('extensions/' + row['locator']['path'] if row['locator']['kind'] == 'extension' else row['locator'].get('path')): row
             for row in catalog['sources'] if row.get('locator', {}).get('kind') in ('extension', 'repository')}
    records = []
    for path in paths:
        scopes = [scope for scope in catalog['discoveryScopes'] if any(fnmatch.fnmatchcase(path, pattern) for pattern in scope['inputs'])]
        if not scopes:
            continue
        source = exact.get(path)
        scope = scopes[0]  # Deliberately ordered specific -> general.
        try:
            inspection = inspect_declarations(confined(repository, path))
        except (OSError, UnicodeError, ValueError, SyntaxError, ET.ParseError) as error:
            inspection = {'status': 'inspection-gap', 'errorKind': type(error).__name__, 'candidates': []}
        records.append({'path': path, 'source': source['id'] if source else None,
                        'disposition': source['disposition'] if source else scope['disposition'],
                        'owner': source.get('owner', scope['owner']) if source else scope['owner'],
                        'purpose': scope['purpose'], 'scope': scope['id'],
                        'available': confined(repository, path).is_file(),
                        'selectedRouted': bool(source and source.get('route', {}).get('via')),
                        'observedConsultation': 'unknown', 'demonstratedApplication': 'not-established-by-discovery',
                        'inspection': inspection, 'limits': scope['limits']})
    for source in catalog['sources']:
        locator = source['locator']
        if locator['kind'] == 'git-history':
            records.append({'path': locator['commit'] + ':' + locator['path'], 'source': source['id'],
                            'disposition': 'history', 'owner': source['owner'], 'purpose': source['purpose'],
                            'available': 'resolve-exact-object-on-demand', 'selectedRouted': False,
                            'observedConsultation': 'unknown', 'demonstratedApplication': 'historical-only',
                            'limits': 'Historical observations do not establish a current defect or supported technology.'})
    # Captures can be packed. Enumerate original logical documents from their
    # original manifest, never infer them from physical files or unpack them.
    profiles = Path(repository) / 'extensions/program-kit-building-blocks/references/dependency-profiles'
    index = profiles / 'index.json'
    if index.is_file():
        for identity, entry in json.loads(index.read_text(encoding='utf-8'))['profiles'].items():
            if not entry.get('knowledge'):
                continue
            manifest = json.loads(confined(profiles, entry['knowledge']['path']).read_text(encoding='utf-8'))
            for document in manifest['documents']:
                records.append({'path': document['publisherPath'], 'source': 'publisher:' + identity + '/' + document['publisherPath'],
                                'profile': identity, 'sourceCommit': manifest['sourceCommit'], 'sha256': document['sha256'],
                                'disposition': 'captured-version', 'owner': 'Exact captured publisher',
                                'purpose': 'Versioned source fact; logical storage resolved through the existing publisher owner.',
                                'available': 'indexed-not-read', 'selectedRouted': False,
                                'observedConsultation': 'unknown', 'demonstratedApplication': 'not-established-by-discovery',
                                'limits': 'A captured document is not framework-wide support or evidence that a consumer read or applied it.'})
    return records


def validate_group(content, identity, declared):
    body = marked(content, identity)
    actual = re.findall(r'<!-- program-kit:knowledge-rule ([^ ]+) -->', body)
    remainder = re.sub(r'<!-- program-kit:knowledge-rule [^>]+ -->.*?<!-- /program-kit:knowledge-rule -->', '', body, flags=re.S)
    if actual != declared or remainder.strip():
        raise ValueError('Unmapped/ambiguous canonical group content: ' + identity)


def validate(catalog, extensions, repository=None):
    source_ids = [row['id'] for row in catalog['sources']]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError('Duplicated canonical source identity')
    for source in catalog['sources']:
        if source['locator']['kind'] not in ('extension', 'repository', 'publisher-capture', 'git-history'):
            raise ValueError('Unknown canonical source kind: ' + source['id'])
        if not source.get('owner') or not source.get('disposition'):
            raise ValueError('Canonical source lacks owner/disposition: ' + source['id'])
    required = {'purpose', 'source', 'selector', 'owner', 'family', 'level', 'applicability', 'exclusions',
                'requiredContext', 'compatibility', 'bindings', 'evidence', 'limits', 'status', 'requirements'}
    owners = set()
    for identity in catalog['rules']:
        rule = effective_rule(catalog, identity)
        if required - rule.keys() or not rule['purpose'] or not rule['owner']:
            raise ValueError('Incomplete canonical rule metadata: ' + identity)
        if rule['family'] not in catalog['knowledgeFamilies'] or rule['level'] not in ('mandatory', 'conditional', 'recommended'):
            raise ValueError('Invalid rule family/level: ' + identity)
        if rule['source'] not in source_ids or not rule['bindings'].get('review'):
            raise ValueError('Canonical rule lacks owner or evaluation route: ' + identity)
        key = (rule['source'], json.dumps(rule['selector'], sort_keys=True))
        if key in owners:
            raise ValueError('Duplicate canonical rule ownership: ' + identity)
        owners.add(key)
        for path in rule['bindings'].get('producers', []) + rule['bindings'].get('checks', []) + rule['bindings'].get('recipes', []):
            if repository is not None and not confined(repository, path).is_file():
                raise ValueError('Missing knowledge execution/evaluation binding: ' + path)
        source = next(row for row in catalog['sources'] if row['id'] == rule['source'])
        kind = source['locator']['kind']
        # Optional mechanisms are resolved only against an actual selected
        # profile. Historical availability does not create an active duty.
        if kind not in ('publisher-capture', 'git-history') and (kind != 'repository' or repository is not None):
            resolve(catalog, identity, extensions=extensions, repository=repository)
    by_requirement = {row['id']: row for row in catalog['requirements']}
    for identity, record in catalog.get('decisionRules', {}).items():
        if record.get('ruleIds'):
            validate_group(confined(extensions, record['source']).read_text(encoding='utf-8'), identity, record['ruleIds'])
    for requirement in catalog['requirements']:
        expected = {leaf for group in requirement.get('decisionRules', []) for leaf in catalog['decisionRules'][group].get('ruleIds', [])}
        if not expected <= set(requirement.get('ruleIds', [])):
            raise ValueError('Omitted canonical duty from responsibility: ' + requirement['id'])
        for identity in requirement.get('ruleIds', []):
            if identity not in catalog['rules'] or requirement['id'] not in catalog['rules'][identity]['requirements']:
                raise ValueError('Stale requirement/canonical rule binding: ' + requirement['id'])
    for identity, rule in catalog['rules'].items():
        for requirement in rule['requirements']:
            if requirement not in by_requirement or identity not in by_requirement[requirement].get('ruleIds', []):
                raise ValueError('Unrouted canonical responsibility binding: ' + identity)
    for row in catalog['migrations']:
        if not row['canonicalRules'] or not set(row['canonicalRules']) <= catalog['rules'].keys() or not row.get('replacementProof'):
            raise ValueError('Incomplete old-to-canonical mapping: ' + row['oldLocation'])


def view(catalog, *, extensions, repository=None, requirements=(), family=None, identities=(), profile=None, resolve_text=False):
    if family and family not in catalog['knowledgeFamilies']:
        raise ValueError('Unknown knowledge family: ' + family)
    chosen = set(identities or (selected(catalog, requirements) if requirements else catalog['rules']))
    unknown = chosen - catalog['rules'].keys()
    if unknown:
        raise ValueError('Unregistered canonical knowledge rule: ' + ', '.join(sorted(unknown)))
    rows = []
    for identity in catalog['rules']:
        rule = effective_rule(catalog, identity)
        if identity not in chosen or family and rule['family'] != family:
            continue
        row = {'id': identity, **rule, 'available': 'not-resolved',
               'selectedRouted': applicable(rule, requirements) if requirements else 'route-declared',
               'observedConsultation': 'unknown', 'demonstratedApplication': 'not-established-by-catalog'}
        if resolve_text:
            try:
                row['resolved'] = resolve(catalog, identity, extensions=extensions, repository=repository, profile=profile)
                row['available'] = True
            except (OSError, ValueError) as error:
                row['available'] = False
                row['diagnostic'] = str(error)
        rows.append(row)
    visible_ids = {row['id'] for row in rows}
    source_ids = {row['source'] for row in rows}
    return {'schemaVersion': 1, 'scope': 'Discovery/routing and selected-source resolution; not application acceptance.',
            'rules': rows, 'sources': [row for row in catalog['sources'] if row['id'] in source_ids or not requirements and not identities and not family],
            'migrations': [row for row in catalog['migrations'] if set(row['canonicalRules']) & visible_ids]}


def render(value):
    lines = ['# Canonical knowledge discovery', '', value['scope'], '',
             'Available, selected/routed, observed consultation and demonstrated application are separate claims.', '']
    for family in dict.fromkeys(row['family'] for row in value['rules']):
        lines += ['## ' + family, '']
        for row in (row for row in value['rules'] if row['family'] == family):
            lines += ['### ' + row['id'], row['purpose'],
                      'Owner: ' + row['owner'] + '; source: ' + row['source'] + '; level: ' + row['level'] + '.',
                      'Applicability: ' + row['applicability'] + ' Exclusions: ' + row['exclusions'],
                      'Available: ' + str(row['available']) + '; selected/routed: ' + str(row['selectedRouted'])
                      + '; observed consultation: unknown; application: not established.',
                      'Evaluation: ' + row['bindings']['review'], 'Limits: ' + row['limits']]
            if 'resolved' in row:
                lines += ['Fingerprint: ' + row['resolved']['fingerprint'], '', row['resolved']['text']]
            if row.get('diagnostic'):
                lines += ['Unresolved: ' + row['diagnostic']]
            lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('catalog', 'scan', 'validate'))
    parser.add_argument('--repository', help='Maintainer tree or selected consumer; never inferred from another checkout')
    parser.add_argument('--installed', action='store_true', help='Do not resolve repository-only sources')
    parser.add_argument('--requirement', action='append', default=[])
    parser.add_argument('--rule', action='append', default=[])
    parser.add_argument('--family')
    parser.add_argument('--profile', help='Explicit exact profile for maintainer publisher lookup')
    parser.add_argument('--resolve', action='store_true')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    args = parser.parse_args()
    catalog = load()
    extensions = Path(__file__).resolve().parents[2]
    repository = Path(args.repository).resolve() if args.repository else None
    try:
        if args.command == 'validate':
            validate(catalog, extensions, None if args.installed else repository)
            value = {'status': 'passed', 'scope': 'Ownership metadata, selectors and declared bindings; no semantic/application acceptance.'}
        elif args.command == 'scan':
            if repository is None or args.installed:
                raise ValueError('Maintainer scan requires --repository and its actual Git tree')
            value = {'scope': 'Broad current-tree discovery; no inferred support or consultation.', 'sources': discover(repository, catalog)}
        else:
            value = view(catalog, extensions=extensions, repository=None if args.installed else repository,
                         requirements=args.requirement, family=args.family, identities=args.rule, profile=args.profile, resolve_text=args.resolve)
        print(json.dumps(value, indent=2, ensure_ascii=False) if args.format == 'json' or args.command != 'catalog' else render(value))
        return 2 if any(row.get('available') is False for row in value.get('rules', [])) else 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
