"""Prepare the reviewed lending-trial scope correction; no agent, acceptance or workflow dispatch."""
import argparse
import json
import os
from pathlib import Path
import sys

ELEMENTS = ['reservation-persistence', 'lifecycle-delivery', 'reservation-database']
RELATIONSHIPS = ['claim-delivery', 'deliver-notification', 'complete-delivery', 'runtime-storage', 'runtime-recipient']
IDENTITY = 'reservation-runtime-acceptance'
ADR = '''# Reservation runtime acceptance scope

- **Status**: Proposed
- **Date**: 2026-09-13
- **Owner**: Architecture maintainer
- **Scope**: Existing RM-01 persistence and delivery semantics; reviewed acceptance correction
- **Supersedes**: closure-evidence-boundary

## Decision for review

Include reservation-persistence, lifecycle-delivery and reservation-database in architecture
acceptance, together with claim-delivery, deliver-notification, complete-delivery,
runtime-storage and runtime-recipient. Preserve their existing ownership, endpoints and
meaning from founding-boundary and founding-durability. This corrects the omitted review
scope; it introduces no provider, package, public API or business-policy change.

The exact items remain Proposed until the governed recovery review is approved. Acceptance
of a design is distinct from proof that RM-01 is implemented. Unrelated proposals stay outside
this correction. The local anonymous trial and deterministic recipient remain the trust boundary.

## Evidence and retained conditions

The four receipts linked by bootstrap-prerequisites.json cover managed runtime admission,
provider durability admission, Forms/hosted-page admission and shell replacement enforcement.
They support the reviewed mechanisms, with their existing limits, not completed reservation
behaviour. Read their exact recipe, source, design and stream bindings. Feature intake still
owns policy edges and the exact brief; feature delivery must prove all transitions and failures.
Reporting, production security, released-reference upgrade and a future internal subscriber
retain their existing named triggers and owners. No new compatibility execution is claimed here.

## Historical decision and current authority

This decision replaces closure-evidence-boundary as current closure bookkeeping and acceptance
scope authority. Preserve that Accepted file unchanged as historical evidence of the earlier
failed recipes, empty conditional transition and deliberately excluded runtime semantics.
Its assertions of open prerequisites and a blocked entry describe that earlier state. The
current prerequisite ledger owns closure evidence, and specification-roadmap.md alone owns
the current entry status. This successor does not copy a transient status into the ADR.

The earlier decision's restrictions on fabricated proofs and bypassed human approval still
apply. The four current mechanism proofs remain required, exact feature confirmation remains
required, and no reporting scaffold, production deployment, real recipient or paid rerun is
authorized by this correction. No original assessment, ratification or Accepted ADR is rewritten.

## Alternatives and consequence

Keeping these semantics excluded would prevent the current reservation slice from proceeding.
Splitting the roadmap is a separate reviewed product-decomposition change, not a workaround
for missing architecture authority. This bounded correction keeps the existing trial scope
and makes its already-described dependencies reviewable before another readiness assessment.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    root = args.project.resolve()
    os.chdir(root)
    sys.path.insert(0, str(root / '.specify/extensions/program-kit-governance/scripts'))
    import bootstrap_recovery as recovery
    import bootstrap_lifecycle as life
    import governance_state as governance
    recovery.manifest(root, args.run_id)
    result = life.load(root / life.RESULT)
    if {item['id'] for item in result['blockers']} != {'rm01-unaccepted-semantics', 'roadmap-status-conflict'}:
        raise ValueError('This fixture repair requires the exact reviewed readiness blockers')
    path = root / f'docs/architecture/decisions/{IDENTITY}.md'
    if path.exists():
        raise ValueError('Recovery is already prepared; validate the preserved review instead of applying it twice')
    model = life.load(root / governance.ARCHITECTURE_MAP)
    for collection, identities in [('elements', ELEMENTS), ('relationships', RELATIONSHIPS)]:
        existing = {item['id']: item for item in model[collection]}
        if any(existing[identity]['status'] != 'proposed' for identity in identities):
            raise ValueError('Correction scope differs from the inspected Proposed architecture')
        for identity in identities:
            existing[identity]['decision_refs'].append(IDENTITY)
    path.write_text(ADR, encoding='utf-8', newline='\n')
    model['decisions'].append({'id': IDENTITY, 'path': path.relative_to(root).as_posix(),
        'sha256': life.digest(path), 'title': 'Reservation runtime acceptance scope', 'date': '2026-09-13',
        'status': 'Proposed', 'scope': 'Existing RM-01 persistence and delivery semantics',
        'owner': 'Architecture maintainer', 'supersedes': ['closure-evidence-boundary']})
    life.write(root / governance.ARCHITECTURE_MAP, model)
    scope = life.load(root / life.SCOPE)
    scope['decisions'][IDENTITY] = {'elements': ELEMENTS, 'relationships': RELATIONSHIPS}
    life.write(root / life.SCOPE, scope)
    ledger = life.load(root / life.LEDGER)
    ledger['sources'].append({'path': path.relative_to(root).as_posix(), 'sha256': life.source_digest(path),
                              'prerequisites': [item['id'] for item in ledger['prerequisites'] if item['disposition'] == 'architecture']})
    life.write(root / life.LEDGER, ledger)
    # Leave room for generated lifecycle/roadmap projections inside the hard budget.
    overview = Path(__file__).parent / 'fixtures/lending-recovery-architecture.md'
    (root / governance.ARCHITECTURE).write_bytes(overview.read_bytes())
    trace = Path(__file__).parent / 'fixtures/lending-recovery-traceability.md'
    (root / governance.TRACEABILITY).write_bytes(trace.read_bytes())
    recovery.synchronize(root, args.run_id)
    review = recovery.review(root, args.run_id)
    bound = recovery.require_prepared_review(root, args.run_id)
    print(json.dumps({'review': review['review'], 'prepared_review_sha256': bound,
                      'changed': sorted(review['changed']), 'accepted': False, 'paid_sessions_started': 0}))


if __name__ == '__main__':
    main()
