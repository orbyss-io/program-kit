"""Validate and append independent assessment data to an owner's intake queue."""
import argparse
import base64
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'extensions/program-kit-governance/scripts'))
import repair_contract as c
import repair_intake as intake
from repair_feedback import write, checkout, now, GitHub, pages, verify_deployment

DISPOSITIONS = ('adopt', 'duplicate', 'defer', 'reject', 'needs-proof')
CAUSES = ('program-kit-defect', 'guidance-gap', 'consumer-choice', 'domain-adaptation', 'mixed', 'unknown')


def validate(value):
    c.fields(value, ('assessmentVersion', 'assessmentId', 'createdAt', 'requests', 'terminologyMapping',
                     'unknownFields', 'evidenceClass', 'expectationSources', 'cause', 'ownership', 'missingProof',
                     'mechanism', 'supportedScope', 'consumerEffects', 'pointOfUseAction', 'relationships',
                     'proposedDisposition', 'rationale', 'correlation'), ('ownerRoute',))
    c.require(value['assessmentVersion'] in ('1.0', '1.1') and re.fullmatch(r'assess-[a-z0-9-]+', value['assessmentId']), 'assessment-version-or-id')
    if value['assessmentVersion'] == '1.1':
        c.require(isinstance(value.get('ownerRoute'), dict), 'assessment-owner-route-required')
    c.require(value['evidenceClass'] in c.CLASSES and value['cause'] in CAUSES and value['proposedDisposition'] in DISPOSITIONS, 'assessment-enums')
    c.require(isinstance(value['requests'], list) and value['requests'], 'assessment-requests')
    for reference in value['requests']:
        c.fields(reference, ('requestId', 'revision', 'requestSha256', 'contractVersion', 'selectedKnowledgeVersion'))
        c.require(re.fullmatch(c.ID, reference['requestId']) and type(reference['revision']) is int and reference['revision'] >= 1
                  and re.fullmatch(c.HEX, reference['requestSha256']), 'assessment-provenance')
    for key in ('createdAt', 'ownership', 'missingProof', 'mechanism', 'supportedScope', 'consumerEffects', 'pointOfUseAction', 'rationale'):
        c.text(value[key])
    for key in ('terminologyMapping', 'unknownFields', 'expectationSources', 'relationships'):
        c.require(isinstance(value[key], list), 'assessment-list')
    for key in ('unknownFields', 'expectationSources'):
        c.require(all(isinstance(x, str) for x in value[key]), 'assessment-string-list')
    for mapping in value['terminologyMapping']:
        c.fields(mapping, ('original', 'canonical', 'reason'))
        c.text(mapping['original']); c.text(mapping['reason'])
        c.require(mapping['canonical'] is None or isinstance(mapping['canonical'], str), 'assessment-canonical-term')
    for relation in value['relationships']:
        c.fields(relation, ('requestId', 'repairId', 'groupId', 'explanation'))
        c.require(any(r['requestId'] == relation['requestId'] for r in value['requests']), 'relationship-provenance')
        pattern = r'repair-[a-z0-9-]+' if value['assessmentVersion'] == '1.0' else intake.REPAIR
        c.require(isinstance(relation['repairId'], str) and re.fullmatch(pattern, relation['repairId'])
                  and (relation['groupId'] is None or isinstance(relation['groupId'], str)), 'repair-or-group-identity')
        c.text(relation['explanation'])
    c.require(isinstance(value['correlation'], dict), 'assessment-correlation')
    c.sensitive(c.encoded(value))
    return value


def submit(root, value):
    root = checkout(root)
    validate(value)
    c.require(value['assessmentVersion'] == '1.1', 'historical-assessment-read-only-use-1.1')
    owner_route = intake.checked_route(root, value['ownerRoute'])
    for reference in value['requests']:
        original = intake.inspect(root, owner_route, reference)
        c.require(original['contractVersion'] == reference['contractVersion'] and
                  original['selectedKnowledgeVersion'] == reference['selectedKnowledgeVersion'], 'assessment-original-version-mismatch')
    path = c.inside(root, 'artifacts/repair-feedback/assessments/' + value['assessmentId'] + '.json')
    write(path, value, immutable=True)
    return {'queuedAssessment': str(path), 'assessmentSha256': c.sha(path.read_bytes()), 'retrievedAt': now(),
            'meaning': 'independent assessment queued; implementation owner disposition required'}


def register_owner(root, owner, ledger):
    root = checkout(root)
    value = {'routeVersion': 1, 'ownerId': owner, 'ledger': ledger, 'adapter': 'items-v1'}
    # Validate before persisting a route, using the same adapter as all readers.
    c.safe_name(ledger)
    content = intake.read(c.inside(root, ledger))
    c.require(isinstance(content, dict) and isinstance(content.get('items'), list), 'owner-ledger-items-adapter-required')
    ids = [item['id'] for item in content['items']]
    c.require(all(isinstance(x, str) and re.fullmatch(intake.REPAIR, x) for x in ids) and len(set(ids)) == len(ids), 'owner-ledger-item-identities')
    write(intake.owner_path(root, owner), value, immutable=True)
    return intake.route(root, owner)


def delivery(root, owner_route, value, digest, source):
    folder = intake.directory(root, value['requestId'], value['revision'])
    record = {'requestId': value['requestId'], 'revision': value['revision'], 'requestSha256': digest,
              'ledger': owner_route['ledger'], 'ownerRoute': owner_route, 'source': source,
              'meaning': 'queued observation; owner disposition required'}
    write(folder / 'delivery.json', record, immutable=True)
    return record


def bind_legacy(root, owner, reference):
    """Owner-selected migration; retains the original immutable delivery bytes."""
    root = checkout(root)
    owner_route = intake.route(root, owner)
    folder = intake.directory(root, reference['requestId'], reference['revision'])
    original = intake.read(folder / 'delivery.json')
    c.require('ownerRoute' not in original and intake.identity(original) == intake.identity(reference) and
              original['ledger'] == owner_route['ledger'], 'legacy-delivery-owner-ledger-mismatch')
    proof = c.guard(folder / 'packet')
    c.require(proof['requestSha256'] == reference['requestSha256'], 'legacy-packet-mismatch')
    binding = intake.identity(reference) | {'ownerRoute': owner_route,
               'originalDeliverySha256': c.sha((folder / 'delivery.json').read_bytes())}
    write(folder / 'owner-binding.json', binding, immutable=True)
    return intake.inspect(root, owner_route, reference)


def preserve_original(root, source, owner=None):
    """Import explicitly selected historical JSON bytes without normalizing answers."""
    root, source = checkout(root), Path(source)
    owner_route = intake.route(root, owner)
    c.require(source.is_file() and source.stat().st_size <= c.MAX_FILE and not source.is_symlink(), 'historical-original-file')
    raw = source.read_bytes()
    value = json.loads(raw)
    c.require(isinstance(value, dict) and isinstance(value.get('requestId'), str) and re.fullmatch(c.ID, value['requestId'])
              and type(value.get('revision')) is int and value['revision'] > 0 and isinstance(value.get('contractVersion'), str)
              and isinstance(value.get('evidence'), dict) and isinstance(value['evidence'].get('knowledgeVersion'), str), 'historical-provenance-required-do-not-invent')
    directory = c.inside(root, f"artifacts/repair-feedback/intake/{value['requestId']}/{value['revision']}")
    original = c.inside(directory, 'packet/request.json')
    original.parent.mkdir(parents=True, exist_ok=True)
    if original.exists(): c.require(original.read_bytes() == raw, 'historical-original-conflict')
    else:
        with original.open('xb') as stream: stream.write(raw)
    imported = {'requestSha256': c.sha(raw), 'contractVersion': value['contractVersion'],
                'selectedKnowledgeVersion': value['evidence']['knowledgeVersion'],
                'source': str(source.resolve()), 'meaning': 'preserved historical account; not normalized or current-contract qualified'}
    write(directory / 'historical-import.json', imported, immutable=True)
    delivery(root, owner_route, value, c.sha(raw), {'kind': 'historical'})
    return imported


def inbox(root, owner, request_id=None, limit=50, after=''):
    root = checkout(root)
    owner_route = intake.route(root, owner)
    c.require(type(limit) is int and 1 <= limit <= 100, 'inbox-limit-1-to-100')
    folders = [intake.directory(root, request_id, 1).parent] if request_id else intake.bounded_files(root / intake.BASE / 'intake', 'rf-*')
    rows, visited = [], 0
    for folder in folders:
        for revision in intake.bounded_files(folder, '*'):
            visited += 1
            c.require(visited <= 1000, 'inbox-bound-exceeded-select-request')
            cursor = folder.name + '/' + revision.name
            if cursor <= after:
                continue
            try:
                record = intake.read(c.inside(revision, 'delivery.json'))
                binding = intake.read(revision / 'owner-binding.json') if (revision / 'owner-binding.json').is_file() else {}
                if record.get('ownerRoute', binding.get('ownerRoute')) != owner_route:
                    if 'ownerRoute' not in record and not binding:
                        rows.append({'cursor': cursor, 'availability': 'invalid-or-unrouted', 'pending': 'unknown'})
                    continue
                data = intake.state(root, owner_route, record)
                rows.append({'cursor': cursor, 'availability': 'available', 'data': data,
                             'pending': data['ownerDecision'] is None})
            except (OSError, ValueError, KeyError, TypeError):
                # Corrupt/unrouted records remain visible; never silently disappear.
                rows.append({'cursor': cursor, 'availability': 'invalid-or-unrouted', 'pending': 'unknown'})
            c.require(len(rows) <= 1000, 'inbox-bound-exceeded-select-request')
    rows.sort(key=lambda row: row['cursor'])
    return {'retrievedAt': now(), 'ownerRoute': owner_route, 'records': rows[:limit],
            'next': rows[limit - 1]['cursor'] if len(rows) > limit else None}


def import_public(root, owner, number, head, base, validator, issue_number, api):
    """Read one explicitly pinned PR as data; writes only the chosen local intake."""
    import repair_evidence_guardian as guardian
    root = checkout(root)
    owner_route = intake.route(root, owner)
    c.require(type(issue_number) is int and issue_number > 0, 'public-import-issue-required')
    deployment = verify_deployment(api, base, validator)
    cache = {}
    def get(endpoint):
        value = api.api('GET', endpoint)
        if '/git/blobs/' in endpoint or '/git/trees/' in endpoint:
            cache[endpoint] = value
        return value
    proof = guardian.inspect(get, c.EVIDENCE, number, head, base, validator)
    marker = f"<!-- program-kit-repair {proof['requestId']} revision={proof['revision']} sha256={proof['requestSha256']} -->"
    issue = api.api('GET', f'repos/{c.UPSTREAM}/issues/{issue_number}')
    bodies = [issue.get('body') or '', *[x.get('body') or '' for x in pages(api, f'repos/{c.UPSTREAM}/issues/{issue_number}/comments')]]
    c.require(any(marker in text for text in bodies), 'public-import-issue-marker-mismatch')
    # Re-read after downloads. Movement pauses import rather than mixing revisions.
    pr = api.api('GET', f'repos/{c.EVIDENCE}/pulls/{number}')
    c.require(pr['head']['sha'] == head and pr['base']['sha'] == base and pr['base']['ref'] == 'main'
              and pr['base']['repo']['full_name'] == c.EVIDENCE, 'public-import-pr-moved')
    checks = []
    for page in range(1, 11):
        batch = api.api('GET', f'repos/{c.EVIDENCE}/commits/{head}/check-runs?per_page=100&page={page}')
        checks.extend(batch['check_runs'])
        if page * 100 >= batch['total_count']:
            break
    else:
        raise ValueError('PKRF public-import-checks-incomplete')
    trusted = []
    for check in checks:
        if check.get('name') != 'program-kit-evidence/guardian' or check.get('app', {}).get('id') != deployment['githubAppId'] or check.get('conclusion') != 'success' or check.get('head_sha') != head:
            continue
        summary = c.load(check.get('output', {}).get('summary', '{}'))
        if all(summary.get(k) == v for k, v in {'submittedCommit': head, 'validatorCommit': validator,
                                               'contractVersion': c.VERSION, 'guardianVersion': c.GUARDIAN}.items()):
            trusted.append(check['id'])
    accepted = False
    prefix = f"requests/{proof['requestId']}/r{proof['revision']}/"
    tree = cache[f'repos/{c.EVIDENCE}/git/trees/{head}?recursive=1']['tree']
    entries = {x['path']: x for x in tree if x['path'].startswith(prefix) and x['type'] != 'tree'}
    if pr.get('merged') is True and trusted:
        merge = pr['merge_commit_sha']
        c.require(isinstance(merge, str) and re.fullmatch(r'[0-9a-f]{40}', merge), 'public-import-merge-commit')
        comparison = api.api('GET', f'repos/{c.EVIDENCE}/compare/{merge}...{deployment["main"]["sha"]}')
        c.require(comparison.get('merge_base_commit', {}).get('sha') == merge and comparison.get('status') in ('ahead', 'identical'), 'public-import-merge-not-on-main')
        merged_tree = api.api('GET', f'repos/{c.EVIDENCE}/git/trees/{merge}?recursive=1')
        c.require(not merged_tree.get('truncated'), 'public-import-merge-tree-incomplete')
        actual = {x['path']: x for x in merged_tree['tree'] if x['path'].startswith(prefix) and x['type'] != 'tree'}
        c.require({p: (x['sha'], x['mode'], x['type']) for p, x in actual.items()} ==
                  {p: (x['sha'], x['mode'], x['type']) for p, x in entries.items()}, 'public-import-accepted-bytes-mismatch')
        accepted = True
    source = {'kind': 'public', 'repository': c.EVIDENCE, 'evidencePR': number, 'commit': head,
              'issueRepository': c.UPSTREAM, 'issue': issue_number, 'validatorCommit': validator}
    folder = intake.directory(root, proof['requestId'], proof['revision'])
    existing = folder / 'delivery.json'
    expected = {'requestId': proof['requestId'], 'revision': proof['revision'], 'requestSha256': proof['requestSha256'],
                'ledger': owner_route['ledger'], 'ownerRoute': owner_route, 'source': source,
                'meaning': 'queued observation; owner disposition required'}
    if existing.exists():
        c.require(intake.read(existing) == expected, 'public-import-existing-delivery-conflict')
    with tempfile.TemporaryDirectory(prefix='repair-public-') as temporary:
        for name, entry in entries.items():
            raw = base64.b64decode(cache[f"repos/{c.EVIDENCE}/git/blobs/{entry['sha']}"]['content'])
            path = c.inside(temporary, name[len(prefix):])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        c.guard(temporary)
        value = intake.read(Path(temporary) / 'request.json')
        if value['revision'] > 1:
            prior = intake.directory(root, value['requestId'], value['revision'] - 1) / 'packet/request.json'
            c.require(prior.is_file() and c.sha(prior.read_bytes()) == value['supersedes'], 'queued-predecessor-required-import-earlier-revision-first')
        for name, raw in c.inventory(temporary).items():
            path = c.inside(folder / 'packet', name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                c.require(path.read_bytes() == raw, 'queued-revision-conflict')
            else:
                with path.open('xb') as stream:
                    stream.write(raw)
    imported = {'source': source, 'requestSha256': proof['requestSha256']}
    write(folder / 'public-import.json', imported, immutable=True)
    delivery(root, owner_route, value, proof['requestSha256'], source)
    observation = {'evidenceAccepted': accepted, 'guardianChecks': sorted(trusted),
                   'mergeCommit': pr.get('merge_commit_sha') if accepted else None,
                   'meaning': 'Observed evidence acceptance only; no defect, implementation or release claim.'}
    observation_path = folder / 'public-observations' / (c.digest(observation) + '.json')
    if not observation_path.exists():
        write(observation_path, observation | {'firstObservedAt': now()}, immutable=True)
    return expected | {'observation': observation, 'retrievedAt': now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--assessment', type=Path)
    action.add_argument('--preserve-original', type=Path)
    parser.add_argument('--owner')
    sub = parser.add_subparsers(dest='command')
    p = sub.add_parser('register-owner'); p.add_argument('--ledger', required=True)
    p = sub.add_parser('inbox'); p.add_argument('--request-id'); p.add_argument('--limit', type=int, default=50); p.add_argument('--after', default='')
    p = sub.add_parser('inspect'); p.add_argument('--request-id', required=True); p.add_argument('--revision', type=int, required=True); p.add_argument('--sha256', required=True)
    p = sub.add_parser('bind-legacy'); p.add_argument('--request-id', required=True); p.add_argument('--revision', type=int, required=True); p.add_argument('--sha256', required=True)
    p = sub.add_parser('import-public'); p.add_argument('--pr', type=int, required=True); p.add_argument('--head', required=True); p.add_argument('--base', required=True); p.add_argument('--validator', required=True); p.add_argument('--issue', type=int, required=True)
    args = parser.parse_args()
    try:
        c.require(sum((bool(args.command), bool(args.assessment), bool(args.preserve_original))) == 1, 'select-one-intake-action')
        if args.command == 'register-owner': result = register_owner(args.root, args.owner, args.ledger)
        elif args.command == 'inbox': result = inbox(args.root, args.owner, args.request_id, args.limit, args.after)
        elif args.command == 'inspect': result = intake.state(checkout(args.root), intake.route(args.root, args.owner),
                                                             {'requestId': args.request_id, 'revision': args.revision, 'requestSha256': args.sha256})
        elif args.command == 'bind-legacy': result = bind_legacy(args.root, args.owner, {'requestId': args.request_id, 'revision': args.revision, 'requestSha256': args.sha256})
        elif args.command == 'import-public': result = import_public(args.root, args.owner, args.pr, args.head, args.base, args.validator, args.issue, GitHub())
        elif args.preserve_original: result = preserve_original(args.root, args.preserve_original, args.owner)
        else: result = submit(args.root, intake.read(args.assessment))
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        print('PKRF assessment-invalid-or-queue-unavailable; original records preserved', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
