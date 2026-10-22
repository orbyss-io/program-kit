"""Resolve attributable knowledge without executing source or changing its authority.

Selectors describe declarations, not evaluated MSBuild, C# semantics or application
correctness. Native tools and independent tests retain those responsibilities.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def effective_rule(catalog, identity):
    if identity not in catalog['rules']:
        raise ValueError('Unregistered canonical knowledge rule: ' + identity)
    defaults, declaration = catalog.get('ruleDefaults', {}), catalog['rules'][identity]
    return {**defaults, **declaration, 'bindings': {**defaults.get('bindings', {}), **declaration.get('bindings', {})}}


def confined(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root):
        raise ValueError('Knowledge source escapes its declared root: ' + str(relative))
    return path


def marked(content, identity, kind='decision-rule'):
    opening = '<!-- program-kit:' + kind + ' ' + identity + ' -->'
    closing = '<!-- /program-kit:' + kind + ' -->'
    matches = re.findall(re.escape(opening) + r'\s*(.*?)\s*' + re.escape(closing), content, re.S)
    if content.count(opening) != 1 or len(matches) != 1 or not matches[0].strip():
        raise ValueError('Missing/ambiguous canonical decision rule: ' + identity)
    return matches[0].strip()


def markdown_headings(content):
    """The shared fence-aware structural reader; headings never infer authority."""
    lines, fenced, headings = content.splitlines(), False, []
    for index, line in enumerate(lines):
        if re.match(r'^\s*(```|~~~)', line):
            fenced = not fenced
        match = re.match(r'^(#{1,6})\s+(.+?)\s*#*$', line) if not fenced else None
        if match:
            headings.append((index, len(match[1]), match[2]))
    return headings


def section_span(content, heading):
    """Return the one actual section body span, without global text replacement."""
    lines, headings = content.splitlines(keepends=True), markdown_headings(content)
    matches = [row for row in headings if row[2] == heading]
    if len(matches) != 1:
        raise ValueError('Missing/ambiguous canonical section: ' + heading)
    start, depth, _ = matches[0]
    end = next((i for i, d, _ in headings if i > start and d <= depth), len(lines))
    return sum(map(len, lines[:start + 1])), sum(map(len, lines[:end]))


def section(content, heading):
    lines, headings = content.splitlines(), markdown_headings(content)
    matches = [row for row in headings if row[2] == heading]
    if len(matches) != 1:
        raise ValueError('Missing/ambiguous canonical section: ' + heading)
    start, depth, _ = matches[0]
    end = next((i for i, d, _ in headings if i > start and d <= depth), len(lines))
    return '\n'.join(lines[start + 1:end]).strip()


def select(content, selector):
    kind = selector['kind']
    if kind == 'document':
        return content.strip()
    if kind == 'markdown-marker':
        return marked(content, selector['id'], selector.get('marker', 'decision-rule'))
    if kind == 'markdown-section':
        value = section(content, selector['heading'])
        if selector.get('excludeDecisionRules'):
            value = re.sub(r'<!-- program-kit:decision-rule [^>]+ -->.*?<!-- /program-kit:decision-rule -->', '', value, flags=re.S)
        return value.strip()
    if kind == 'json-pointer':
        document = json.loads(content)
        pointer = selector['pointer']
        if pointer and not pointer.startswith('/'):
            raise ValueError('JSON Pointer must be empty or start with /')

        def at(location):
            value = document
            try:
                for part in location.split('/')[1:] if location else ():
                    key = part.replace('~1', '/').replace('~0', '~')
                    value = value[int(key)] if isinstance(value, list) else value[key]
                return value
            except (KeyError, IndexError, ValueError, TypeError) as error:
                raise ValueError('Missing canonical JSON Pointer: ' + location) from error

        value, references, external = at(pointer), {}, set()

        def dependencies(node):
            if isinstance(node, dict):
                for key, child in node.items():
                    if key in ('$ref', '$dynamicRef') and isinstance(child, str):
                        if child.startswith('#/') and child not in references:
                            references[child] = at(child[1:])
                            dependencies(references[child])
                        elif not child.startswith('#/'):
                            external.add(child)
                    else:
                        dependencies(child)
            elif isinstance(node, list):
                for child in node:
                    dependencies(child)

        dependencies(value)
        return json.dumps({'selected': value, 'localReferences': references, 'unresolvedReferences': sorted(external)}, ensure_ascii=False, sort_keys=True, indent=2)
    if kind == 'python-symbol':
        tree = ast.parse(content)
        symbols = {}
        for node in tree.body:
            names = ([node.name] if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else
                     [target.id for target in node.targets if isinstance(target, ast.Name)] if isinstance(node, ast.Assign) else
                     [node.target.id] if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) else [])
            for name in names:
                symbols.setdefault(name, []).append(node)
        seen, selected = set(), []

        def visit(name):
            if name in seen:
                return
            rows = symbols.get(name, [])
            if len(rows) != 1:
                raise ValueError('Missing/ambiguous canonical Python symbol: ' + name)
            seen.add(name)
            node = rows[0]
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                for dependency in sorted({item.id for item in ast.walk(node.value) if isinstance(item, ast.Name)} & symbols.keys()):
                    visit(dependency)
            selected.append(ast.get_source_segment(content, node))

        visit(selector['name'])
        return '\n\n'.join(selected)
    if kind == 'xml-elements':
        tree = ET.fromstring(content)
        matches = []
        # Ancestor conditions/imports are part of declaration context, not an
        # assertion that this declaration is the effective project value.
        def walk(node, ancestors):
            local = node.tag.rsplit('}', 1)[-1]
            if local == selector['element'] and all(node.get(k) == v for k, v in selector.get('attributes', {}).items()):
                matches.append({'ancestors': ancestors, 'element': ET.tostring(node, encoding='unicode')})
            for child in node:
                walk(child, ancestors + [{'element': local, 'attributes': dict(node.attrib)}])
        walk(tree, [])
        if not matches:
            raise ValueError('Missing canonical XML declaration: ' + selector['element'])
        return json.dumps({'declarations': matches, 'imports': [dict(n.attrib) for n in tree.iter() if n.tag.rsplit('}', 1)[-1] == 'Import']}, sort_keys=True, indent=2)
    if kind == 'editorconfig-key':
        current, matches, context = None, [], []
        for line in content.splitlines():
            if line.strip().startswith('[') and line.strip().endswith(']'):
                current = line.strip()
            key, separator, value = line.partition('=')
            if separator and key.strip().lower() in (selector['key'].lower(), 'root'):
                context.append({'section': current, 'key': key.strip(), 'value': value.strip()})
            if separator and key.strip().lower() == selector['key'].lower() and current == selector['section']:
                matches.append(value.strip())
        if not matches:
            raise ValueError('Missing canonical EditorConfig declaration: ' + selector['key'])
        return json.dumps({'section': current if current == selector['section'] else selector['section'], 'key': selector['key'],
                           'orderedValues': matches, 'declarationContext': context, 'effectiveConfiguration': False}, sort_keys=True)
    raise ValueError('Unsupported knowledge selector: ' + str(kind))


def source_bytes(locator, *, extensions, repository=None, profile=None):
    kind = locator['kind']
    if kind in ('extension', 'repository'):
        root = extensions if kind == 'extension' else repository
        if root is None:
            raise ValueError('Repository-only knowledge is unavailable in installed context: ' + locator['path'])
        path = confined(root, locator['path'])
        if not path.is_file():
            raise ValueError('Missing canonical knowledge source: ' + locator['path'])
        return path.read_bytes(), {'kind': kind, 'path': locator['path']}
    if kind == 'git-history':
        if repository is None:
            raise ValueError('Historical Git source is unavailable in installed context')
        commit = locator['commit']
        if not re.fullmatch(r'[a-f0-9]{40}', commit):
            raise ValueError('Historical knowledge requires an exact commit')
        confined(repository, locator['path'])
        result = subprocess.run(['git', 'show', commit + ':' + locator['path']], cwd=repository,
                                capture_output=True, timeout=15)
        if result.returncode:
            raise ValueError('Historical knowledge object is unavailable: ' + commit + ':' + locator['path'])
        return result.stdout, dict(locator)
    if kind == 'publisher-capture':
        scripts = confined(extensions, 'program-kit-building-blocks/scripts')
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        import building_blocks as blocks
        if profile:
            registry = Path(extensions) / 'program-kit-building-blocks/references/dependency-profiles'
            identity = profile
            index = blocks.load_json(registry / 'index.json')
            blocks.qualified_dependency_profile(registry, identity, blocks.load_json(blocks.default_catalog(Path(blocks.__file__))))
            binding = index['profiles'][identity].get('knowledge')
            if not binding:
                raise ValueError('Exact selected profile lacks publisher knowledge: ' + identity)
            capture = blocks.load_json(confined(registry, binding['path']))
        else:
            if repository is None:
                raise ValueError('Publisher knowledge requires an explicit profile or selected consumer context')
            effective = blocks.effective_dependency_context(Path(repository))
            registry, identity, capture = Path(effective['registryPath']), effective['profile'], effective['publisherKnowledge']
            if not capture:
                raise ValueError('Exact selected profile lacks publisher knowledge; no default substituted')
        rows = [row for row in capture['documents'] if row['publisherPath'] == locator['document']]
        if len(rows) != 1:
            raise ValueError('Missing/ambiguous exact publisher document: ' + locator['document'])
        row = rows[0]
        value = blocks.publisher_document_bytes(registry, row)
        if hashlib.sha256(value).hexdigest() != row['sha256']:
            raise ValueError('Publisher document digest mismatch: ' + locator['document'])
        return value, {'kind': kind, 'profile': identity, 'sourceCommit': capture['sourceCommit'],
                       'document': row['publisherPath'], 'sha256': row['sha256']}
    raise ValueError('Unsupported knowledge source kind: ' + str(kind))


def resolve(catalog, identity, *, extensions, repository=None, profile=None):
    rule = effective_rule(catalog, identity)
    rows = [source for source in catalog['sources'] if source.get('id') == rule['source']]
    if len(rows) != 1:
        raise ValueError('Missing/ambiguous canonical owner: ' + identity)
    source = rows[0]
    raw, provenance = source_bytes(source['locator'], extensions=extensions, repository=repository, profile=profile)
    content = raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    if rule.get('withinDecisionRule'):
        marked(content, rule['withinDecisionRule'])
    value = select(content, rule['selector'])
    if not value.strip():
        raise ValueError('Empty canonical knowledge rule: ' + identity)
    # Selected declarations and routing/compatibility changes invalidate derived
    # proof. Other text in the same file does not invalidate an unrelated rule.
    fingerprint = digest(json.dumps({'rule': rule, 'content': value, 'publisher': provenance if provenance['kind'] == 'publisher-capture' else None}, sort_keys=True))
    return {'id': identity, 'text': re.sub(r'<!-- /?program-kit:[^>]+ -->\s*', '', value).strip(),
            'fingerprint': fingerprint, 'sourceSha256': hashlib.sha256(raw).hexdigest(), 'provenance': provenance,
            'owner': rule['owner'], 'limits': rule['limits']}
