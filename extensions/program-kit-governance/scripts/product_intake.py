"""Optional inspection of readable product context; never records human acceptance.

Skills preserve explicit decisions in product intent, constitution and ADRs.
This helper inspects supplied artifacts without authoring receipts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import governance_state as governance


def inspect(root: Path | None = None, *, require_intent: bool = False) -> dict:
    root = (root or Path.cwd()).resolve()
    intent = root / governance.PROJECT_INTENT
    if require_intent and (not intent.is_file() or not intent.read_text(encoding='utf-8').strip()):
        raise ValueError('Product inspection requires a nonempty docs/architecture/project-intent.md')
    artifacts, findings = [], []
    for relative in (governance.PROJECT_INTENT, governance.CONSTITUTION, governance.ARCHITECTURE,
                     governance.ROADMAP, Path('docs/architecture/technology-radar.md')):
        path = root / relative
        if path.is_file():
            if not path.read_text(encoding='utf-8').strip():
                raise ValueError('Empty authored document: ' + relative.as_posix())
            artifacts.append(relative.as_posix())
    map_path = root / governance.ARCHITECTURE_MAP
    if map_path.is_file():
        import architecture_map
        architecture_map.validate_model(architecture_map.load_object(map_path), root)
        artifacts.append(governance.ARCHITECTURE_MAP.as_posix())
    for path in sorted((root / governance.DECISIONS).glob('*.md')):
        if not path.read_text(encoding='utf-8').strip():
            raise ValueError('Empty ADR: ' + str(path.relative_to(root)))
        artifacts.append(path.relative_to(root).as_posix())
    if not intent.is_file():
        findings.append('No product intent recorded; use product-intake or continue with the explicit current request.')
    return {'status': 'CONTEXT AVAILABLE' if intent.is_file() else 'NO RECORDED CONTEXT',
            'artifacts': artifacts, 'findings': findings,
            'next_action': 'Review substantive decisions with the human, then continue to specification intake.',
            'authority': 'Human decisions in readable documents; inspection supplies no confirmation, ratification or runtime acceptance.'}


def validate_draft() -> dict:
    return inspect(require_intent=True)


def review() -> dict:
    """Return links to actual documents rather than another review dossier."""
    return inspect(require_intent=True)


def status() -> dict:
    return inspect()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'review', 'validate', 'status'))
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(require_intent=args.command in {'review', 'validate'}), ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Product inspection failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
