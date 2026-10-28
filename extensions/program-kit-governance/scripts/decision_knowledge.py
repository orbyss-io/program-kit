"""Read decision constraints from their canonical references, without a second summary."""
from pathlib import Path
import re
from knowledge_sources import marked, resolve
from knowledge_discovery import display_coverage


def decision_rule(extensions, record, identity):
    path = (extensions / record['source']).resolve()
    if not path.is_relative_to(extensions.resolve()):
        raise ValueError('Knowledge source escapes installed extensions')
    content = path.read_text(encoding='utf-8')
    value = marked(content, identity)
    return re.sub(r'<!-- /?program-kit:knowledge-rule[^>]* -->\s*', '', value).strip()


def constraints(catalog, requirements, extensions, detailed=False):
    """Only selected rules are loaded. Shared constraints appear once per brief."""
    selected, seen, scopes = {}, set(), {}
    selected_rules = {identity for row in requirements for identity in row.get('ruleIds', [])}
    tags = set().union(*(set(row['selectionTags']) for row in requirements if 'selectionTags' in row))
    tags = tags if any('selectionTags' in row for row in requirements) else None
    for requirement in requirements:
        rows, focused, examples = [], [], []
        if 'ruleIds' in requirement:
            for identity in requirement['ruleIds']:
                if identity in seen:
                    continue
                value = resolve(catalog, identity, extensions=extensions)
                rule = catalog['rules'][identity]
                text = value['text']
                if not detailed and rule.get('display') == 'focused-detail':
                    display_coverage(catalog, identity, extensions, selected_rules=selected_rules, tags=tags)
                    focused.append(identity)
                    seen.add(identity)
                    continue
                if not detailed and rule.get('display') == 'focused-example':
                    display_coverage(catalog, identity, extensions, selected_rules=selected_rules, tags=tags)
                    examples.append(identity)
                    seen.add(identity)
                    continue
                location = ' (' + value['provenance']['path'] + ')' if detailed else ''
                qualifier = ''
                if rule.get('profileScope') or rule.get('when'):
                    applicability = rule['applicability']
                    if applicability not in scopes:
                        scopes[applicability] = 'scope-' + str(len(scopes) + 1)
                        rows.append(scopes[applicability] + ' applicability: ' + applicability)
                    qualifier = ' [' + scopes[applicability] + ']'
                rows.append('Canonical ' + identity + location + qualifier + ':\n' + text)
                seen.add(identity)
            if focused:
                rows.append('Focused canonical detail (--only ' + requirement['id'] + '): ' + ', '.join(focused) + '.')
            if examples:
                rows.append('Versioned examples (--only ' + requirement['id'] + '): ' + ', '.join(examples)
                            + '; match their captured baselines before reuse.')
            if not rows:
                rows.append('Shared canonical duties are shown above; use --only ' + requirement['id'] + ' for this responsibility.')
            selected[requirement['id']] = rows
            continue
        for identity in requirement.get('decisionRules', []):
            if identity not in seen:
                if identity not in catalog.get('decisionRules', {}):
                    raise ValueError('Unregistered canonical decision rule: ' + identity)
                rows.append(decision_rule(extensions, catalog['decisionRules'][identity], identity))
                seen.add(identity)
        selected[requirement['id']] = rows
    return selected
