"""Execute producer-authored bootstrap probes between native workflow agent stages."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from bootstrap_lifecycle import LEDGER, LifecycleError, load, write, run_proof, validate_prerequisites, validate_recipe

PLAN = Path('docs/architecture/bootstrap-proof-plan.json')


def require_first_slice_plan(root, plan, ledger, records):
    """Validate the selected handoff without requiring complete provider knowledge.

    Every supplied recipe and every claimed promotion is still checked by execute.
    Unplanned prerequisites stay open and gate their affected phase.
    """
    from bootstrap_handoff import first_feature
    first_feature(root)


def invalidate_changed_recipes(root, plan, ledger):
    """Retain receipts while reopening only changed execution inputs before acceptance."""
    import copy
    import uuid
    from bootstrap_lifecycle import digest, design_digest, local, proof_tooling
    from governance_state import ROADMAP, roadmap_records
    updated = copy.deepcopy(ledger)
    planned = {p['id']: p for p in plan['probes']}
    invalidated = []
    for item in updated['prerequisites']:
        if item['id'] not in planned or item['status'] != 'closed':
            continue
        stale = []
        for evidence in item['evidence']:
            if evidence['kind'] != 'compatibility':
                continue
            path = local(root, evidence['path'])
            if digest(path) != evidence['sha256']:
                raise LifecycleError('Preserved proof receipt changed; restore its integrity before retry')
            proof = load(path)
            if any(not local(root, p).is_file() or design_digest(local(root, p)) != h for p, h in proof.get('design_sources', {}).items()):
                raise LifecycleError('Selected design/pins changed; reopen the owning decision before replanning compatibility')
            for bound in proof.get('streams', []) + ([proof['test_result']] if proof.get('test_result') else []):
                if digest(local(root, bound['path'])) != bound['sha256']:
                    raise LifecycleError('Preserved proof diagnostics changed; restore their integrity before retry')
            recipe, contract, _, _ = validate_recipe(root, item['id'], planned[item['id']]['recipe'])
            required = {(p.relative_to(root).as_posix(), digest(p)) for p in (recipe, contract)}
            changed = not required <= {(b['path'], b['sha256']) for b in proof.get('inputs', [])} or proof.get('tooling_sources') != proof_tooling() or any(
                not local(root, b['path']).is_file() or digest(local(root, b['path'])) != b['sha256'] for b in proof.get('inputs', []))
            if changed:
                stale.append(evidence)
        if stale:
            if (root / '.specify/governance/bootstrap-approval.json').is_file():
                raise LifecycleError('Accepted compatibility inputs changed; reopen the architecture review before renewal')
            item['status'] = 'open'
            item['evidence'] = [e for e in item['evidence'] if e not in stale]
            invalidated.append(item['id'])
    if not invalidated:
        return ledger
    # Validate the new recipe contracts before revoking any existing eligibility.
    for probe in plan['probes']:
        validate_recipe(root, probe['id'], probe['recipe'])
    path = root / ROADMAP
    original = path.read_text(encoding='utf-8')
    affected = {s for i in updated['prerequisites'] if i['id'] in invalidated for s in i['affected_slices']}
    if any(r['id'] in affected and r['Status'] in {'Active', 'Delivered'} for r in roadmap_records(path)):
        raise LifecycleError('Active/delivered scope needs an explicit compatibility change review')
    text = original
    for identity in affected:
        pattern = r'(^###\s+' + re.escape(identity) + r':[^\n]*\n)(.*?)(?=^###\s+|\Z)'
        text = re.sub(pattern, lambda m: m[1] + re.sub(r'(?m)^(-\s+\*\*Status\*\*:\s*)Ready$', r'\g<1>Blocked', m[2]), text, flags=re.MULTILINE | re.DOTALL)
    archive = root / '.specify/governance/compatibility/invalidations' / (uuid.uuid4().hex + '.json')
    write(archive, {'reason': 'execution-inputs-changed', 'prerequisites': invalidated, 'previous_ledger': ledger, 'previous_roadmap': original})
    # Conservative ordering: a stopped process may leave Blocked with old evidence,
    # never Ready with revoked evidence. The next resume can repeat reconciliation.
    path.write_text(text, encoding='utf-8')
    write(root / LEDGER, updated)
    return updated


def require_proven_closure(root: Path):
    """Read-only admission for explicit reuse after deterministic repair."""
    from governance_state import roadmap_records, ROADMAP
    from json_schema import validate_value
    from bootstrap_lifecycle import digest
    plan = load(root / PLAN)
    schema = Path(__file__).resolve().parents[1] / 'references/bootstrap-proof-plan.schema.json'
    if not validate_value(plan, load(schema), schema)['valid'] or not plan['probes']:
        raise LifecycleError('Proven closure reuse requires a nonempty valid proof plan')
    validate_prerequisites(root, roadmap_records(root / ROADMAP), required=True, allow_proposed_authority=True)
    items = {i['id']: i for i in load(root / LEDGER)['prerequisites']}
    require_first_slice_plan(root, plan, load(root / LEDGER), roadmap_records(root / ROADMAP))
    for probe in plan['probes']:
        item = items.get(probe['id'])
        if item is None or item['disposition'] != 'architecture' or item['status'] != 'closed':
            raise LifecycleError('Every planned architecture proof must pass before closure reuse')
        recipe, contract, _, _ = validate_recipe(root, probe['id'], probe['recipe'])
        required = {(p.relative_to(root).as_posix(), digest(p)) for p in [recipe, contract]}
        if not any(required <= {(p['path'], p['sha256']) for p in load(root / evidence['path'])['inputs']}
                   for evidence in item['evidence'] if evidence['kind'] == 'compatibility'):
            raise LifecycleError('Current planned recipe/contract has no matching passing proof')
    return [p['id'] for p in plan['probes']]


def execute(root: Path, *, validate_only=False):
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
    if not validate_only:
        ledger = invalidate_changed_recipes(root, plan, ledger)
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
    require_first_slice_plan(root, plan, ledger, records)
    # Validate the whole plan before executing any probe. Successful receipts are
    # reusable on explicit native resume; current evidence is checked above.
    for probe in probes:
        validate_recipe(root, probe['id'], probe['recipe'])
    if validate_only:
        return []
    results = []
    for probe in probes:
        item = items[probe['id']]
        if item['status'] == 'closed':
            continue
        result = run_proof(root, probe['id'], probe['recipe'], probe['timeout'])
        results.append(result)
        if result['exit_code']:
            proof = load(root / result['path'])
            # A bounded negative result is useful research, not a broken workflow.
            # Do not attach it as closure evidence or promote its dependent slice.
            expected = proof.get('failure_category') == 'needs-provisioning'
            if proof.get('failure_category') == 'verification-failed' and proof.get('test_result'):
                from phase_obligations import test_results
                cases = test_results(root / proof['test_result']['path'], 'junit')
                expected = bool(cases) and all(name in cases for name in proof['checks']) and not all(cases.values())
            if expected:
                continue
            from compatibility_diagnostics import sanitize
            detail = next(((root / s['path']).read_text(encoding='utf-8') for s in proof.get('streams', []) if s['path'].endswith('stderr.txt')), '')
            raise LifecycleError('Compatibility failed (' + str(proof.get('failure_category', 'verification-failed'))
                                 + '); inspect ' + result['path'] + '. Repair the reported condition, then resume this same run; unchanged recipes are not reauthored.\n' + sanitize(detail)[-1600:])
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
