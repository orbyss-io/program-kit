"""Require the configured host to equal selected public immutable availability evidence."""
import argparse
import json
from pathlib import Path
import re


def verify(evidence, reference):
    matches = [x for x in evidence.get('artifacts', []) if x.get('packageKey') == 'oci:ghcr.io/orbyss-io/foundation-host']
    if len(matches) != 1 or matches[0].get('status') != 'manifest-digest':
        raise ValueError('Accepted building-block selection must supply exactly one public Foundation host digest.')
    expected = matches[0].get('reference', '')
    if not re.fullmatch(r'ghcr.io/orbyss-io/foundation-host@sha256:[a-f0-9]{64}', expected) or reference != expected:
        raise ValueError('Configured host digest differs from selected public-availability evidence.')
    return matches[0]


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--reference',required=True)
    args=parser.parse_args()
    try:
        verify(json.loads(args.evidence.read_text(encoding='utf-8')),args.reference)
    except (ValueError,OSError) as error:
        parser.exit(2,str(error)+'\n')
