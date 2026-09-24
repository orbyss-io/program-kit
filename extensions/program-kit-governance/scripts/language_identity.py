"""Canonical known language identities; never infer adoption from arbitrary prose."""
import re

ALIASES = {'c#': 'c#', 'csharp': 'c#', 'c sharp': 'c#', '.net': '.net',
           'dotnet': '.net', 'c#/.net': 'c#', 'c# / .net': 'c#',
           'typescript': 'typescript', 'javascript': 'javascript', 'html': 'html', 'css': 'css'}
QUALIFIERS = {'managed default', 'program kit default', 'program-kit default',
              'program-kit-default', '.net managed default', 'explicit selection'}


def canonical_language(value: str) -> str:
    label = ' '.join(value.strip().casefold().split())
    match = re.fullmatch(r'(.+?)\s*\(([^()]*)\)', label)
    if match and match[1].strip() in ALIASES and match[2] in QUALIFIERS:
        label = match[1].strip()
    # Unknown labels remain constraints, including compound/qualified alternate stacks.
    return ALIASES.get(label, label)
