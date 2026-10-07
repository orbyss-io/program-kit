"""Read decision constraints from their canonical references, without a second summary."""
from pathlib import Path
import re


def decision_rule(extensions, record, identity):
    path = (extensions / record['source']).resolve()
    if not path.is_relative_to(extensions.resolve()):
        raise ValueError('Knowledge source escapes installed extensions')
    content = path.read_text(encoding='utf-8')
    pattern = (r'<!-- program-kit:decision-rule ' + re.escape(identity)
               + r' -->\s*(.*?)\s*<!-- /program-kit:decision-rule -->')
    matches = re.findall(pattern, content, re.S)
    if len(matches) != 1 or not matches[0].strip():
        raise ValueError('Missing/ambiguous canonical decision rule: ' + identity)
    return matches[0].strip()


def constraints(catalog, requirements, extensions):
    """Only selected rules are loaded. Shared constraints appear once per brief."""
    selected, seen = {}, set()
    for requirement in requirements:
        rows = []
        for identity in requirement.get('decisionRules', []):
            if identity not in seen:
                if identity not in catalog.get('decisionRules', {}):
                    raise ValueError('Unregistered canonical decision rule: ' + identity)
                rows.append(decision_rule(extensions, catalog['decisionRules'][identity], identity))
                seen.add(identity)
        selected[requirement['id']] = rows
    return selected
