"""Explicit fictional review authoring for deterministic engine tests only."""
def fictional_claims(coding, source_path, checks, review='review.md'):
    groups = {}
    for duty in coding['evaluation']['duties']:
        groups.setdefault((duty.get('reviewFamily', duty['rule']), duty['owner']), []).append(duty['rule'])
    inspections = [{'rules': rules, 'sources': [{'path': source_path, 'start': 1, 'end': 1}],
                    'boundary': 'Fictional workflow artifact under deterministic test',
                    'findings': ['Synthetic authoring exercises admission only; no real semantic or human acceptance claim.'],
                    'assessment': 'Fictional authored inspection for canonical family ' + family}
                   for (family, owner), rules in groups.items()]
    from operation_readiness import LIMIT_RULE, limit_review_targets
    for inspection in inspections:
        if LIMIT_RULE in inspection['rules']:
            inspection['limitReconciliation'] = [
                {'operation': operation, 'limit': identity, 'disposition': 'compliant',
                 'assessment': 'Explicit fictional reconciliation only; executable fixture owns any actual finite behavior claim.'}
                for operation, identity in sorted(limit_review_targets(coding), key=lambda pair: (pair[0], pair[1] or ''))]
    return [{'rules': [rule for rules in groups.values() for rule in rules], 'checks': checks, 'review': review,
             'authorship': {'implementationAuthors': ['fictional-implementer'], 'reviewer': 'fictional-independent-reviewer', 'kind': 'agent'},
             'inspections': inspections,
             'conclusion': 'Synthetic authored workflow review; assertions belong to the executable fixture.',
             'limits': 'Fictional review and attribution; no arbitrary agent behavior or real consumer correctness.'}
            ]
