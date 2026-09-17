"""One consumer WEB-Q definition source and a deterministic tooling view."""
from pathlib import Path
import re

SOURCE = Path('docs/architecture/quality-attributes.md')
TARGET = Path('docs/architecture/quality-system.md')
START = '<!-- PROGRAM-KIT:QUALITY-CASES:START -->'
END = '<!-- PROGRAM-KIT:QUALITY-CASES:END -->'
DEFINITION = re.compile(r'^\s*[-*]\s+(?:\*\*|`)?(WEB-Q\d+)(?:\*\*|`)?(?=[\s:(])')


def definitions(text):
    cases = {}
    current = None
    for line in text.splitlines():
        match = DEFINITION.match(line)
        if match:
            current = match[1]
            if current in cases:
                raise ValueError(f'Duplicate consumer quality case: {current}')
            cases[current] = [line.strip()]
        elif current and line[:1].isspace() and line.strip():
            cases[current].append(line.rstrip())
        else:
            current = None
    return {key: '\n'.join(lines) for key, lines in cases.items()}


def projection(root):
    path = root / SOURCE
    return {'source': SOURCE.as_posix(), 'cases': definitions(path.read_text(encoding='utf-8')) if path.is_file() else {}}


def outside_view(text):
    if START not in text and END not in text:
        return text
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) >= text.index(END):
        raise ValueError('Malformed generated consumer quality-case view')
    return text[:text.index(START)] + text[text.index(END) + len(END):]


def synchronize(root):
    cases = projection(root)['cases']
    path = root / TARGET
    if not path.is_file():
        return []
    original = path.read_text(encoding='utf-8')
    outside = outside_view(original)
    authored = definitions(outside)
    if authored:
        raise ValueError('Consumer WEB-Q definitions belong only in quality-attributes.md; '
                         'remove duplicate tooling definitions and reference the generated view: ' + ', '.join(authored))
    if not cases and START not in original:
        return []
    view = '\n'.join([START, '## Consumer quality cases', '',
                      '> Generated from [quality attributes](quality-attributes.md); edit definitions there.', '',
                      *cases.values(), END])
    if START in original:
        result = original[:original.index(START)] + view + original[original.index(END) + len(END):]
    else:
        result = original.rstrip() + '\n\n' + view + '\n'
    if result != original:
        path.write_text(result, encoding='utf-8')
    return list(cases)


def validate(root):
    path = root / TARGET
    if not path.is_file():
        return
    text = path.read_text(encoding='utf-8')
    expected = projection(root)['cases']
    outside = outside_view(text)
    if definitions(outside):
        raise ValueError('Tooling duplicates consumer WEB-Q definitions; use the generated quality-case view')
    if expected and START not in text:
        raise ValueError('Missing generated consumer quality-case view in quality-system.md')
    actual = definitions(text[text.index(START):text.index(END)]) if START in text else {}
    if expected != actual:
        raise ValueError('Consumer quality-case view is stale; synchronize it from quality-attributes.md')
