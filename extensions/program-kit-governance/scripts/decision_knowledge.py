"""Read decision constraints from their canonical references, without a second summary."""
from pathlib import Path
import re
from knowledge_sources import marked, resolve


def decision_rule(extensions, record, identity):
    path = (extensions / record['source']).resolve()
    if not path.is_relative_to(extensions.resolve()):
        raise ValueError('Knowledge source escapes installed extensions')
    content = path.read_text(encoding='utf-8')
    value = marked(content, identity)
    return re.sub(r'<!-- /?program-kit:knowledge-rule[^>]* -->\s*', '', value).strip()


def constraints(catalog, requirements, extensions, detailed=False):
    """Only selected rules are loaded. Shared constraints appear once per brief."""
    selected, seen = {}, set()
    for requirement in requirements:
        rows = []
        if 'ruleIds' in requirement:
            focused = []
            previewed = False
            has_principles = any(identity.startswith('principle.') for identity in requirement['ruleIds'])
            for identity in requirement['ruleIds']:
                if identity in seen:
                    continue
                value = resolve(catalog, identity, extensions=extensions)
                rule = catalog['rules'][identity]
                text = value['text']
                if not detailed and rule.get('display') == 'focused-example':
                    rows.append('Versioned example: --only ' + requirement['id'] + '; match its captured baseline before reuse.')
                    seen.add(identity)
                    continue
                # Essential marked constraints remain complete. Focused sections
                # are linked excerpts in the ordinary brief, complete in --only.
                if not detailed and identity.startswith('guidance.'):
                    focused.append(identity)
                    if previewed or has_principles:
                        seen.add(identity)
                        continue
                    previewed = True
                    if len(text) > 180:
                        text = text[:180].rsplit(' ', 1)[0] + ' … [excerpt]'
                location = ' (' + value['provenance']['path'] + ')' if detailed else ''
                rows.append('Canonical ' + identity + location + ':\n' + text)
                seen.add(identity)
            if focused:
                rows.append('Complete canonical sources: --only ' + requirement['id'] + ' (' + str(len(focused)) + ' sections).')
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
