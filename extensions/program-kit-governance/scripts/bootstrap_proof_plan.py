"""Execute producer-authored bootstrap probes between native workflow agent stages."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from bootstrap_lifecycle import LEDGER, LifecycleError, load, write, run_proof, validate_prerequisites, validate_recipe

PLAN = Path('docs/architecture/bootstrap-proof-plan.json')


def execute(root: Path):
    from governance_state import roadmap_records, ROADMAP
    plan = load(root / PLAN)
    from json_schema import validate_value
    schema_path = Path(__file__).resolve().parents[1] / 'references/bootstrap-proof-plan.schema.json'
    result = validate_value(plan, load(schema_path), schema_path)
    if not result['valid']:
        raise LifecycleError('Bootstrap proof plan violates its schema: ' + str(result['errors']))
    if set(plan) - {'$schema'} != {'schemaVersion', 'probes', 'readyWhenProven'} or plan['schemaVersion'] != 1:
        raise LifecycleError('Bootstrap proof plan requires schemaVersion 1, probes and readyWhenProven')
    ledger = load(root / LEDGER)
    records = roadmap_records(root / ROADMAP)
    validate_prerequisites(root, records, required=True, allow_proposed_authority=True)
    items = {item['id']: item for item in ledger['prerequisites']}
    probes = plan['probes']
    if not isinstance(probes, list) or any(not isinstance(p, dict) or set(p) != {'id', 'recipe', 'timeout'} for p in probes):
        raise LifecycleError('Each bootstrap probe needs id, recipe and timeout')
    ids = [p['id'] for p in probes]
    if len(ids) != len(set(ids)) or any(identity not in items or items[identity]['disposition'] != 'architecture' for identity in ids):
        raise LifecycleError('Probe IDs must identify distinct architecture prerequisites')
    if any(type(p['timeout']) is not int or not 1 <= p['timeout'] <= 600 for p in probes):
        raise LifecycleError('Probe timeout must be between 1 and 600 seconds')
    promotions = plan['readyWhenProven']
    if not isinstance(promotions, list) or any(not isinstance(p, dict) or set(p) != {'id', 'prerequisites', 'rationale'} for p in promotions):
        raise LifecycleError('Conditional readiness needs id, prerequisites and reviewed rationale')
    by_id = {r['id']: r for r in records}
    if len({p['id'] for p in promotions}) != len(promotions):
        raise LifecycleError('Duplicate conditional readiness entry')
    for promotion in promotions:
        identity = promotion['id']
        required = {i['id'] for i in items.values() if i['disposition'] == 'architecture' and identity in i['affected_slices']}
        if identity not in by_id or by_id[identity]['Status'] not in {'Blocked', 'Candidate', 'Ready'} or not isinstance(promotion['rationale'], str) or not promotion['rationale'].strip():
            raise LifecycleError('Conditional readiness must name an existing eligible candidate and rationale')
        if not required or set(promotion['prerequisites']) != required or any(items[i]['status'] != 'closed' and i not in ids for i in required):
            raise LifecycleError('Conditional readiness must cover every affected architecture prerequisite')
    # Validate the whole plan before executing any probe. Successful receipts are
    # reusable on explicit native resume; current evidence is checked above.
    for probe in probes:
        validate_recipe(root, probe['id'], probe['recipe'])
    results = []
    for probe in probes:
        item = items[probe['id']]
        if item['status'] == 'closed':
            continue
        result = run_proof(root, probe['id'], probe['recipe'], probe['timeout'])
        results.append(result)
        if result['exit_code']:
            raise LifecycleError('Compatibility failed; inspect ' + result['path'] + ' before an explicit resume')
        item['evidence'].append({k: result[k] for k in ('path', 'sha256', 'kind')})
        item['status'] = 'closed'
        write(root / LEDGER, ledger)
    # The producer names exact conditional transitions; this executor changes no
    # substantive scope or authority and final review still owns acceptance.
    path = root / ROADMAP
    original = path.read_text(encoding='utf-8')
    updated = original
    for promotion in promotions:
        identity = promotion['id']
        if all(items[i]['status'] == 'closed' for i in promotion['prerequisites']):
            pattern = r'(^###\s+' + re.escape(identity) + r':[^\n]*\n)(.*?)(?=^###\s+|\Z)'
            def promote(match):
                return match[1] + re.sub(r'(?m)^(-\s+\*\*Status\*\*:\s*)(Blocked|Candidate)$', r'\g<1>Ready', match[2])
            updated, count = re.subn(pattern, promote, updated, flags=re.MULTILINE | re.DOTALL)
            if count != 1:
                raise LifecycleError('Ambiguous roadmap identity for conditional readiness')
    path.write_text(updated, encoding='utf-8')
    try:
        validate_prerequisites(root, roadmap_records(path), required=True, allow_proposed_authority=True)
    except Exception:
        path.write_text(original, encoding='utf-8')
        raise
    return results


if __name__ == '__main__':
    import json
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='.')
    args = parser.parse_args()
    try:
        print(json.dumps({'proofs': execute(Path(args.repository).resolve())}))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
