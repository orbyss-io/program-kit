"""Observable repair-feedback acceptance with recording fakes; zero public writes."""
from __future__ import annotations
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'extensions/program-kit-governance/scripts')]
import repair_contract as c
import repair_feedback as rf
import repair_intake as intake
import repair_evaluator as evaluator
import repair_evidence_guardian as guardian
import repair_guardian_check as guardian_check
import build_repair_contract
import prepare_evidence_repository
import consumer_upgrade

BASE, HEAD, TRUSTED = 'a' * 40, 'b' * 40, 'c' * 40


def member(path, data):
    return {'path': path, 'purpose': 'minimal synthetic proof', 'provenance': 'fictional fixture, no consumer data',
            'bytes': len(data), 'sha256': c.sha(data), 'transformations': [], 'qualification': 'synthetic fixture reviewed'}


def packet(root, previous=None, suffix='packet'):
    root = root / suffix
    root.mkdir()
    value = rf.draft('synthetic-project', 'PKRF100 fails after scoped retry', 'governance', previous)
    value['originalAccount'] = 'Original consumer wording: sprocket boundary, unclassified.'
    value['unclassified'] = ['sprocket boundary']
    value['evidence'].update(programKitVersion='0.12.5', profileVersion='retained-0.12', knowledgeVersion='knowledge-old')
    value['diagnostics']['decision'].update(answer='Later explanation only', explanationKind='retrospective', evidenceClass='reported')
    value['diagnostics']['results'].update(answer='Inspected failed synthetic log; no independent run', evidenceClass='inspected')
    files = {'report.md': b'# Synthetic repair observation\nExpected X, observed Y. No independent reproduction.\n',
             'evidence/repro.py': b'raise RuntimeError("Do not execute submitted code")\n'}
    value['evidence']['members'] = [member(n, d) for n, d in files.items()]
    for n, data in files.items():
        path = root / n; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    rf.write(root / 'request.json', value)
    return root, value


def init(root, contributor=False):
    root.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
    if contributor:
        for name in ('extensions/program-kit-governance/extension.yml', '.agents/skills/program-kit-repair-evaluator/SKILL.md', 'docs/owner-ledger.json'):
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('{}\n', encoding='utf-8')
        rf.write(root / 'docs/owner-ledger.json', {'approval': 'Synthetic existing approval preserved', 'items': [{'id': 'U0', 'status': 'planned'}]})
        evaluator.register_owner(root, 'maintenance', 'docs/owner-ledger.json')
    return root


def assessment(owner, packets, name='synthetic'):
    references = [{'requestId': value['requestId'], 'revision': value['revision'],
                   'requestSha256': c.sha((directory / 'request.json').read_bytes()),
                   'contractVersion': value['contractVersion'], 'selectedKnowledgeVersion': value['evidence']['knowledgeVersion']}
                  for directory, value in packets]
    return {'assessmentVersion': '1.1', 'assessmentId': 'assess-' + name, 'createdAt': rf.now(),
            'ownerRoute': intake.route(owner, 'maintenance'), 'requests': references,
            'terminologyMapping': [], 'unknownFields': ['root cause'], 'evidenceClass': 'inspected',
            'expectationSources': ['synthetic retained guidance'], 'cause': 'unknown', 'ownership': 'unknown',
            'missingProof': 'Independent execution missing', 'mechanism': 'Potential shared guidance gap',
            'supportedScope': 'Synthetic observations', 'consumerEffects': 'unknown', 'pointOfUseAction': 'Identify next action',
            'relationships': [{'requestId': r['requestId'], 'repairId': 'U0', 'groupId': None, 'explanation': 'Existing synthetic finding'} for r in references],
            'proposedDisposition': 'needs-proof', 'rationale': 'Evidence is not independent execution', 'correlation': {'availability': 'pending'}}


def owner_decision(owner, value, disposition='adopt', facts=None):
    path = owner / value['ownerRoute']['ledger']
    ledger = rf.read(path)
    extension = ledger.setdefault('repairFeedback', {'adapterVersion': 1, 'ownerRoute': value['ownerRoute'], 'decisions': []})
    for reference in value['requests']:
        extension['decisions'].append(intake.identity(reference) | {
            'assessmentId': value['assessmentId'], 'assessmentSha256': c.sha((owner / intake.BASE / 'assessments' / (value['assessmentId'] + '.json')).read_bytes()),
            'disposition': disposition, 'rationale': 'Synthetic owner decision; approval history retained',
            'repairIds': ['U0'] if disposition in ('adopt', 'duplicate') else [], 'facts': facts or {}})
    rf.write(path, ledger)


def correlation(destination=7):
    return {'retrievedAt': 'fixture-time', 'complete': True,
            'queries': [{'query': 'repo:orbyss-io/program-kit is:issue state:closed PKRF100', 'bound': 10, 'total': 1, 'incomplete': False}],
            'candidates': [{'issue': {'number': destination, 'state': 'closed', 'body': 'Older fix with same trigger'}, 'comments': []}]}


class RecordingGitHub:
    """Stateful public API fake; response loss happens after an actual fake mutation."""
    def __init__(self):
        self.calls, self.writes, self.issues, self.comments, self.forks, self.refs, self.prs, self.commits = [], [], [], {}, [], [], [], {}
        self.loss, self.lost = None, False
        self.issue_state = 'open'
        self.fail_read = False
        self.rules = {'enforcement': 'active', 'target': 'branch', 'bypass_actors': [], 'source_type': 'Repository', 'source': c.EVIDENCE,
            'conditions': {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}},
            'rules': [{'type': 'required_status_checks', 'parameters': {'strict_required_status_checks_policy': False,
                      'required_status_checks': [{'context': guardian_check.CHECK, 'integration_id': 123}]}},
                      {'type': 'pull_request', 'parameters': {'required_approving_review_count': 1, 'dismiss_stale_reviews_on_push': True,
                                                            'require_code_owner_review': True, 'require_last_push_approval': True,
                                                            'required_review_thread_resolution': True}}, {'type': 'deletion'}, {'type': 'non_fast_forward'}]}
        self.app = {'id': 123, 'owner': {'login': 'orbyss-io'},
                    'permissions': {'checks': 'write', 'contents': 'read', 'pull_requests': 'read', 'metadata': 'read'}}
        self.source_moved = False

    def auth(self):
        return 'fixture-user'

    def api(self, method, endpoint, payload=None):
        self.calls.append((method, endpoint, deepcopy(payload)))
        if method != 'GET': self.writes.append((method, endpoint, deepcopy(payload)))
        if self.fail_read and method == 'GET': raise ValueError('PKRF fake-unavailable')
        result = self.handle(method, endpoint, payload)
        if method != 'GET' and self.loss and self.loss in endpoint and not self.lost:
            self.lost = True
            raise ValueError('PKRF simulated-response-loss')
        return deepcopy(result)

    def handle(self, method, endpoint, payload):
        path, _, query = endpoint.partition('?')
        params = parse_qs(query)
        if method == 'GET':
            if path == 'apps/program-kit-evidence-guardian': return self.app
            if path == 'repos/' + c.EVIDENCE: return {'full_name': c.EVIDENCE, 'private': False, 'default_branch': 'main', 'id': 42}
            if path.endswith('/commits/main'): return {'sha': BASE, 'commit': {'tree': {'sha': 'base-tree'}}}
            if path.endswith('/contents/guardian-deployment.json'):
                return {'content': base64.b64encode(c.encoded({'contractVersion': c.VERSION, 'validatorCommit': TRUSTED,
                    'repositoryRulesetId': 1, 'githubAppId': 123, 'githubAppSlug': 'program-kit-evidence-guardian'})).decode()}
            if '/rulesets/' in path: return self.rules
            if '/rules/branches/main' in path: return [dict(r, ruleset_id=1) for r in self.rules['rules']]
            if '/contents/' in path: return {'sha': 'changed' if self.source_moved and params.get('ref') != [TRUSTED] else 'trusted-blob'}
            if path == 'repos/fixture-user/program-kit-evidence': return {'full_name': 'fixture-user/program-kit-evidence', 'parent': {'full_name': c.EVIDENCE}, 'html_url': 'https://github.com/fixture-user/program-kit-evidence'}
            if path.endswith('/forks'): return self.forks
            if '/git/matching-refs/' in path: return self.refs
            if '/git/commits/' in path: return self.commits[path.rsplit('/', 1)[-1]]
            if path.endswith('/pulls'): return self.prs
            if path.endswith('/issues'):
                return self.issues if params.get('page', ['1'])[0] == '1' else []
            if path.endswith('/comments'):
                number = int(path.split('/')[-2]); return self.comments.get(number, [])
            if '/issues/' in path:
                number = int(path.rsplit('/', 1)[-1])
                issue = next((i for i in self.issues if i['number'] == number), {'number': number, 'body': 'Existing closed older fix'})
                return dict(issue, state=self.issue_state, updated_at='source-updated', html_url=f'https://github.com/{c.UPSTREAM}/issues/{number}')
            if '/pulls/' in path:
                if path.endswith('/reviews'): return []
                return {'head': {'sha': HEAD}, 'state': self.issue_state, 'updated_at': 'source-pr-time'}
            if '/check-runs' in path: return {'check_runs': [{'name': 'guardian', 'conclusion': self.issue_state}], 'total_count': 1}
            if path.endswith('/statuses'): return []
            if '/releases/' in path: return {'tag_name': 'fixture-release', 'published_at': 'source-release-time'}
        if method == 'POST':
            if path == f'repos/{c.UPSTREAM}/issues':
                obj = dict(payload, number=11, html_url=f'https://github.com/{c.UPSTREAM}/issues/11')
                self.issues.append(obj); return obj
            if path.endswith('/comments'):
                number = int(path.split('/')[-2]); rows = self.comments.setdefault(number, [])
                obj = dict(payload, html_url=f'https://github.com/{c.UPSTREAM}/issues/{number}#issuecomment-{len(rows)+1}')
                rows.append(obj); return obj
            if path.endswith('/forks'):
                obj = {'full_name': 'fixture-user/program-kit-evidence'}; self.forks.append(obj); return obj
            if path.endswith('/git/blobs'):
                return {'sha': hashlib.sha1(base64.b64decode(payload['content'])).hexdigest()}
            if path.endswith('/git/trees'): return {'sha': c.digest(payload)}
            if path.endswith('/git/commits'):
                obj = {'sha': HEAD, 'tree': {'sha': payload['tree']}, 'parents': [{'sha': p} for p in payload['parents']]}
                self.commits[HEAD] = obj; return obj
            if path.endswith('/git/refs'):
                obj = {'ref': payload['ref'], 'object': {'sha': payload['sha']}}; self.refs.append(obj); return obj
            if path.endswith('/pulls'):
                obj = dict(payload, number=12, html_url=f'https://github.com/{c.EVIDENCE}/pull/12', head={'sha': HEAD}, base={'ref': payload['base']})
                self.prs.append(obj); return obj
        raise AssertionError((method, endpoint, payload))


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='repair-feedback-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.consumer = init(self.root / 'consumer')
        self.owner = init(self.root / 'owner', contributor=True)
        self.packet, self.value = packet(self.root)

    def test_contract_schema_and_historical_answers_are_preserved(self):
        from jsonschema import Draft202012Validator
        generated = build_repair_contract.build()
        published = ROOT / 'extensions/program-kit-governance/references/repair-feedback'
        for name, value in generated.items(): self.assertEqual(c.encoded(value), (published / name).read_bytes())
        schema = Draft202012Validator(generated['request.schema.json'])
        schema.validate(self.value)
        c.request(self.value)
        for key, replacement in [('component', 'guessed-new-category'), ('revision', 0), ('supersedes', 'bad'), ('contractVersion', '9.0')]:
            invalid = dict(self.value, **{key: replacement})
            self.assertTrue(list(schema.iter_errors(invalid)))
            with self.assertRaises(ValueError): c.request(invalid)
        next_packet, revision = packet(self.root, self.value, 'revision')
        self.assertEqual(self.value['requestId'], revision['requestId'])
        self.assertEqual(c.sha((self.packet / 'request.json').read_bytes()), revision['supersedes'])
        self.assertEqual('knowledge-old', self.value['evidence']['knowledgeVersion'])
        self.assertEqual(['sprocket boundary'], self.value['unclassified'])
        self.assertEqual('retrospective', self.value['diagnostics']['decision']['explanationKind'])
        self.assertEqual('inspected', self.value['diagnostics']['results']['evidenceClass'])
        self.assertNotEqual(c.guard(self.packet)['requestSha256'], c.guard(next_packet)['requestSha256'])
        with self.assertRaisesRegex(ValueError, 'duplicate-json-field'): c.load('{"a":1,"a":2}')

    def test_ignored_personal_state_is_outside_inputs_and_preserved_by_reconfigure(self):
        before = consumer_upgrade.inputs(self.consumer)
        disclosure = rf.configure(self.consumer, 'contributor', self.owner, 'maintenance')
        self.assertTrue(disclosure['ignoreVerified'])
        self.assertIn('disclosure', disclosure)
        self.assertEqual(before, consumer_upgrade.inputs(self.consumer))
        rf.remember(self.consumer, {'requestId': self.value['requestId'], 'route': 'local', 'projectId': 'synthetic-project'})
        index = (self.consumer / rf.PERSONAL / 'submissions.json').read_bytes()
        rf.configure(self.consumer, 'consumer')
        self.assertEqual(index, (self.consumer / rf.PERSONAL / 'submissions.json').read_bytes())
        self.assertEqual(before, consumer_upgrade.inputs(self.consumer))
        with self.assertRaises(ValueError): rf.remember(self.consumer, {'status': 'fixed'})
        with self.assertRaises(ValueError): rf.configure(self.consumer, 'contributor', self.consumer)
        with patch.object(rf, 'git', return_value=str(self.owner) + '/.'):
            self.assertEqual(self.owner.resolve(), rf.checkout(self.owner))
        with patch.object(rf, 'git', return_value=str(self.consumer)):
            with self.assertRaisesRegex(ValueError, 'checkout-root-required'): rf.checkout(self.owner)

    def test_local_queue_durable_idempotent_zero_public_mutation_and_fresh_ledger(self):
        rf.configure(self.consumer, 'contributor', self.owner, 'maintenance')
        api = RecordingGitHub()
        with patch.object(rf, 'GitHub', side_effect=AssertionError('Local route touched GitHub')):
            first = rf.local(self.consumer, self.packet, 'docs/owner-ledger.json')
            self.assertEqual(first, rf.local(self.consumer, self.packet, 'docs/owner-ledger.json'))
        self.assertEqual([], api.writes)
        self.assertEqual('pending', first['correlation']['availability'])
        records = rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']
        before = rf.status(records)
        self.assertIsNone(before['sources'][0]['data']['ownerDecision'])
        value = assessment(self.owner, [(self.packet, self.value)])
        evaluator.submit(self.owner, value)
        owner_decision(self.owner, value, 'defer', {'validated': {'value': False, 'proof': ['Synthetic owner inspection']}})
        after = rf.status(records)
        self.assertEqual('defer', after['sources'][0]['data']['ownerDecision']['disposition'])
        self.assertTrue(after['lifecycle']['assessed'])
        self.assertFalse(after['lifecycle']['validated'])
        self.assertEqual('unknown', after['lifecycle']['released'])
        self.assertEqual('local', after['sources'][0]['source'])
        self.assertNotIn('ownerDisposition', (self.consumer / rf.PERSONAL / 'submissions.json').read_text())
        changed = deepcopy(self.value); changed['title'] = 'Conflicting correction without revision'
        rf.write(self.packet / 'request.json', changed)
        with self.assertRaisesRegex(ValueError, 'queued-revision-conflict'): rf.local(self.consumer, self.packet, 'docs/owner-ledger.json')

    def test_queue_revisions_require_exact_predecessor(self):
        rf.configure(self.consumer, 'contributor', self.owner, 'maintenance')
        second, value = packet(self.root, self.value, 'second')
        with self.assertRaisesRegex(ValueError, 'predecessor'): rf.local(self.consumer, second, 'docs/owner-ledger.json')
        rf.local(self.consumer, self.packet, 'docs/owner-ledger.json')
        rf.local(self.consumer, second, 'docs/owner-ledger.json')
        self.assertEqual(2, len(rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']))

    def test_prepare_measures_derivative_without_changing_originals(self):
        original = c.inventory(self.packet)
        value = deepcopy(self.value)
        for m in value['evidence']['members']: m.update(bytes=0, sha256='0' * 64, transformations=['selected sanitized synthetic excerpt'])
        rf.write(self.packet / 'request.json', value)
        before = c.inventory(self.packet)
        sealed = self.root / 'sealed'
        rf.prepare(self.packet, sealed)
        self.assertEqual(before, c.inventory(self.packet))
        self.assertEqual(c.sha(original['report.md']), rf.read(sealed / 'request.json')['evidence']['members'][0]['sha256'])
        c.guard(sealed)

    def test_guard_rejects_tamper_extra_policy_archive_secret_and_size_without_echo(self):
        for name, data in [('evidence/repro.py', b'tamper'), ('extra.md', b'extra'), ('guardian.py', b'policy'),
                           ('evidence/archive.zip', b'archive'), ('evidence/secret.log', b'ghp_' + b'x' * 30),
                           ('evidence/large.txt', b'x' * (c.MAX_FILE + 1))]:
            with self.subTest(name=name):
                target = self.packet / name
                original = target.read_bytes() if target.exists() else None
                target.write_bytes(data)
                with self.assertRaises(ValueError) as error: c.guard(self.packet)
                self.assertNotIn('ghp_', str(error.exception))
                if original is None: target.unlink()
                else: target.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'sensitive'): c.sensitive(b'Authorization: Bearer secret-value')

    def test_guard_rejects_path_alias_hardlink_and_escape(self):
        for name in ('../escape', '/absolute', 'evidence/x:ads.txt', 'evidence/NUL.txt', 'evidence/a//b', 'evidence/a/../b'):
            with self.assertRaises(ValueError): c.safe_name(name)
        linked = self.packet / 'evidence/alias.txt'
        os.link(self.packet / 'report.md', linked)
        with self.assertRaisesRegex(ValueError, 'hardlink'): c.guard(self.packet)
        linked.unlink()
        if os.name != 'nt':
            linked.symlink_to(self.packet / 'report.md')
            with self.assertRaisesRegex(ValueError, 'linked'): c.guard(self.packet)

    def test_supported_types_binary_qualification_and_manifest_budgets(self):
        data = b'%PDF-1.7\nsynthetic-data-never-rendered'
        target = self.packet / 'evidence/fixture.pdf'; target.write_bytes(data)
        self.value['evidence']['members'].append(member('evidence/fixture.pdf', data))
        rf.write(self.packet / 'request.json', self.value)
        c.guard(self.packet)
        self.value['evidence']['members'][-1]['qualification'] = 'unknown'
        rf.write(self.packet / 'request.json', self.value)
        with self.assertRaisesRegex(ValueError, 'qualification'): c.guard(self.packet)

    def test_bounded_open_closed_search_refines_empty_and_excessive_and_inspects_comments(self):
        api = RecordingGitHub()
        original = api.handle
        queries = []
        def handle(method, endpoint, payload):
            if endpoint.startswith('search/issues'):
                query = unquote(endpoint); queries.append(query)
                if 'initial' in query and 'state:open' in query: return {'total_count': 0, 'items': []}
                if 'initial' in query and 'state:closed' in query: return {'total_count': 21, 'items': []}
                return {'total_count': 1, 'items': [{'number': 7}], 'incomplete_results': False}
            return original(method, endpoint, payload)
        api.handle = handle
        result = rf.search(api, 'initial', 'alternate', 'narrow')
        self.assertTrue(result['complete'])
        self.assertEqual(4, len(queries))
        self.assertTrue(all('repo:orbyss-io/program-kit' in q for q in queries))
        self.assertEqual(1, len(result['candidates']))
        self.assertTrue(any('/comments?' in path for _, path, _ in api.calls))
        self.assertEqual([], api.writes)
        result = rf.search(api, 'initial', 'alternate')
        self.assertFalse(result['complete'])

    def review(self, destination='new'):
        return rf.plan(self.packet, correlation(), destination, 'Same trigger and inspected causal boundary; previous closed version differs.',
                       'fixture-user', BASE, TRUSTED)

    def test_review_binds_destinations_all_content_and_exact_approval(self):
        rf.configure(self.consumer, 'consumer')
        review = self.review()
        api = RecordingGitHub()
        with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, 'unapproved', api)
        self.assertEqual([], api.calls)
        review['body'] += '\nUnexpected addition'
        with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        self.assertEqual([], api.writes)
        with self.assertRaisesRegex(ValueError, 'duplicate-check'): rf.plan(self.packet, {'complete': False}, 'new', 'reason', 'fixture-user', BASE, TRUSTED)
        with self.assertRaisesRegex(ValueError, 'destination'): self.review(99)

    def test_public_new_and_duplicate_exact_inventory_and_idempotent_retries(self):
        for destination in ('new', 7):
            with self.subTest(destination=destination):
                consumer = init(self.root / str(destination))
                rf.configure(consumer, 'consumer')
                api = RecordingGitHub(); review = self.review(destination)
                receipt = rf.public(consumer, self.packet, review, review['reviewDigest'], api)
                before = len([w for w in api.writes if not w[1].endswith(('/git/blobs', '/git/trees'))])
                again = rf.public(consumer, self.packet, review, review['reviewDigest'], api)
                self.assertEqual(receipt['issue'], again['issue'])
                self.assertEqual(before, len([w for w in api.writes if not w[1].endswith(('/git/blobs', '/git/trees'))]))
                self.assertEqual(1 if destination == 'new' else 0, len(api.issues))
                self.assertEqual(1, len(api.prs))
                self.assertEqual(1, len(api.forks))
                self.assertEqual(1, len(api.refs))
                for _, path, payload in api.writes:
                    self.assertFalse(path.startswith('repos/' + c.EVIDENCE + '/git/'))
                    if path.endswith('/git/trees'):
                        self.assertEqual({review['prefix'] + '/' + name for name in review['files']}, {e['path'] for e in payload['tree']})
                self.assertIn('knowledge-old', review['body'])
                self.assertIn('retrospective', review['body'])
                self.assertTrue(all(x['kind'] in ('issue', 'evidence-pr') for x in rf.read(consumer / rf.PERSONAL / 'submissions.json')['requests'][0]['objects']))

    def test_public_response_loss_reconciles_issue_comment_fork_branch_pr_and_crosslink(self):
        scenarios = [('new', '/issues'), (7, '/comments'), ('new', '/forks'), ('new', '/git/refs'), ('new', '/pulls')]
        for index, (destination, loss) in enumerate(scenarios):
            with self.subTest(loss=loss):
                consumer = init(self.root / ('loss' + str(index))); rf.configure(consumer, 'consumer')
                api = RecordingGitHub(); api.loss = loss; review = self.review(destination)
                with self.assertRaisesRegex(ValueError, 'response-loss'): rf.public(consumer, self.packet, review, review['reviewDigest'], api)
                self.assertTrue(list((consumer / rf.PERSONAL / 'delivery').rglob('*.json')))
                rf.public(consumer, self.packet, review, review['reviewDigest'], api)
                self.assertEqual(1 if destination == 'new' else 0, len(api.issues))
                self.assertEqual(1, len(api.forks)); self.assertEqual(1, len(api.refs)); self.assertEqual(1, len(api.prs))
                self.assertEqual(1 if destination == 'new' else 2, sum(map(len, api.comments.values())))

    def test_public_rejects_same_name_guardian_rules_and_wrong_destination_before_writes(self):
        rf.configure(self.consumer, 'consumer'); review = self.review()
        for change in ('same-name-check', 'bypass', 'wrong-repository', 'source-moved', 'no-review', 'wrong-app', 'broad-app', 'wrong-owner', 'inactive-check', 'base-rewrite-required'):
            api = RecordingGitHub()
            if change == 'same-name-check': api.rules['rules'][0] = {'type': 'required_status_checks', 'parameters': {'required_status_checks': [{'context': 'guardian'}]}}
            elif change == 'bypass': api.rules['bypass_actors'] = [{'actor_id': 1}]
            elif change == 'wrong-repository': api.rules['source'] = 'other/repo'
            elif change == 'source-moved': api.source_moved = True
            elif change == 'wrong-app': api.rules['rules'][0]['parameters']['required_status_checks'][0]['integration_id'] = 124
            elif change == 'broad-app': api.app['permissions']['contents'] = 'write'
            elif change == 'wrong-owner': api.app['owner']['login'] = 'untrusted'
            elif change == 'inactive-check': api.rules['enforcement'] = 'disabled'
            elif change == 'base-rewrite-required': api.rules['rules'][0]['parameters']['strict_required_status_checks_policy'] = True
            else: api.rules['rules'][1]['parameters']['require_last_push_approval'] = False
            with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
            self.assertEqual([], api.writes)
        api = RecordingGitHub(); original = api.handle
        def unprovisioned(method, endpoint, payload):
            if '/contents/guardian-deployment.json?' in endpoint:
                return {'content': base64.b64encode((ROOT / 'evidence-repository/guardian-deployment.json').read_bytes()).decode()}
            return original(method, endpoint, payload)
        api.handle = unprovisioned
        with self.assertRaisesRegex(ValueError, 'not-configured'): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        self.assertEqual([], api.writes)

    def test_public_retry_after_main_advances_keeps_reviewed_bytes_and_parent(self):
        rf.configure(self.consumer, 'consumer'); api = RecordingGitHub(); review = self.review()
        api.loss = '/git/refs'
        with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        original = api.handle
        def advanced(method, endpoint, payload):
            if endpoint.endswith('/commits/main'): return {'sha': 'd' * 40, 'commit': {'tree': {'sha': 'later-tree'}}}
            if '/compare/' in endpoint: return {'merge_base_commit': {'sha': BASE}, 'status': 'ahead'}
            if endpoint.endswith('/commits/' + BASE): return {'sha': BASE, 'commit': {'tree': {'sha': 'base-tree'}}}
            return original(method, endpoint, payload)
        api.handle = advanced
        rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        self.assertEqual(1, len(api.refs)); self.assertEqual(1, len(api.prs))
        self.assertEqual([{'sha': BASE}], api.commits[HEAD]['parents'])

    def test_interrupted_issue_outside_reconciliation_bound_uses_recovered_reference(self):
        rf.configure(self.consumer, 'consumer'); api = RecordingGitHub(); review = self.review()
        api.loss = '/issues'
        with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        original = api.handle
        def outside_recent(method, endpoint, payload):
            if method == 'GET' and endpoint.startswith('repos/' + c.UPSTREAM + '/issues?'): return []
            return original(method, endpoint, payload)
        api.handle = outside_recent
        with self.assertRaisesRegex(ValueError, 'unresolved'): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        rf.recover(self.consumer, api, 'synthetic-project', [{'repository': c.UPSTREAM, 'kind': 'issue', 'number': 11}])
        rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        self.assertEqual(1, len(api.issues)); self.assertEqual(1, len(api.prs))

    def test_fresh_status_changed_remote_and_failed_reads_never_fall_back(self):
        rf.configure(self.consumer, 'consumer')
        records = [{'route': 'public', 'objects': [
            {'repository': c.UPSTREAM, 'number': 7, 'kind': 'issue'},
            {'repository': c.EVIDENCE, 'number': 8, 'kind': 'evidence-pr'},
            {'repository': c.UPSTREAM, 'number': 9, 'kind': 'implementation-pr'},
            {'repository': c.UPSTREAM, 'number': 10, 'kind': 'release'}]}]
        before = (self.consumer / rf.PERSONAL / 'submissions.json').read_bytes()
        api = RecordingGitHub(); first = rf.status(records, api)
        api.issue_state = 'closed'; second = rf.status(records, api)
        self.assertEqual('open', first['sources'][0]['data']['state'])
        self.assertEqual('closed', second['sources'][0]['data']['state'])
        self.assertEqual('closed', second['sources'][1]['checks'][0]['conclusion'])
        self.assertTrue(all(value == 'unknown' for value in second['lifecycle'].values()))
        api.fail_read = True; third = rf.status(records, api)
        self.assertTrue(all(s['availability'] == 'unavailable' for s in third['sources']))
        self.assertTrue(all('data' not in s for s in third['sources']))
        self.assertEqual(before, (self.consumer / rf.PERSONAL / 'submissions.json').read_bytes())
        self.assertIn('retrievedAt', third)
        self.assertTrue(all('search/' not in path for _, path, _ in api.calls))

    def test_actual_gh_adapter_disables_cache_and_suppresses_stderr(self):
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')) as run:
            rf.GitHub('explicit-fixture-gh').api('GET', 'user')
            command = run.call_args.args[0]
            self.assertNotIn('--cache', command)
            self.assertIn('Cache-Control: no-cache, no-store', command)
            rf.GitHub('explicit-fixture-gh').api('GET', 'repos/' + c.EVIDENCE + '/compare/' + BASE + '...' + HEAD)
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'Bearer secret-value')):
            with self.assertRaises(ValueError) as error: rf.GitHub('fixture').api('GET', 'user')
            self.assertNotIn('secret-value', str(error.exception))
        with patch.object(shutil, 'which', return_value=None), patch.object(Path, 'is_file', return_value=True):
            with self.assertRaisesRegex(ValueError, 'outside-PATH'): rf.GitHub()
        with patch.object(shutil, 'which', return_value=None), patch.object(Path, 'is_file', return_value=False):
            with self.assertRaisesRegex(ValueError, 'absent'): rf.GitHub()

    def test_account_discovery_includes_commented_and_involved_project_provenance(self):
        api = RecordingGitHub(); original = api.handle
        def handle(method, endpoint, payload):
            if endpoint.startswith('search/issues'):
                return {'total_count': 1, 'items': [{'number': 7}], 'incomplete_results': False}
            if '/issues/7' in endpoint and not '/comments' in endpoint:
                return {'number': 7, 'body': 'Someone else authored this issue'}
            if '/issues/7/comments' in endpoint:
                return [{'body': 'program-kit-repair project `synthetic-project` evidence'}]
            return original(method, endpoint, payload)
        api.handle = handle
        result = rf.discover(api, 'fixture-user', 'synthetic-project')
        self.assertEqual('project', result['scope']); self.assertTrue(result['objects'])
        queries = ' '.join(result['queries'])
        for qualifier in ('author:', 'commenter:', 'involves:'): self.assertIn(qualifier, queries)
        self.assertEqual([], rf.discover(api, 'fixture-user', 'different-project')['objects'])
        self.assertEqual('account', rf.discover(api, 'fixture-user')['scope'])

    def test_evaluator_multiple_requests_one_repair_owner_ledger_unchanged(self):
        rf.configure(self.consumer, 'contributor', self.owner, 'maintenance')
        rf.local(self.consumer, self.packet, 'docs/owner-ledger.json')
        another, other = packet(self.root, suffix='another')
        rf.local(self.consumer, another, 'docs/owner-ledger.json')
        references = [{'requestId': value['requestId'], 'revision': value['revision'], 'requestSha256': c.sha((directory / 'request.json').read_bytes()),
                       'contractVersion': value['contractVersion'], 'selectedKnowledgeVersion': value['evidence']['knowledgeVersion']}
                      for directory, value in ((self.packet, self.value), (another, other))]
        assessment = {'assessmentVersion': '1.1', 'ownerRoute': intake.route(self.owner, 'maintenance'), 'assessmentId': 'assess-synthetic', 'createdAt': rf.now(), 'requests': references,
            'terminologyMapping': [{'original': 'sprocket boundary', 'canonical': None, 'reason': 'unclassified'}], 'unknownFields': ['root cause'],
            'evidenceClass': 'inspected', 'expectationSources': ['old selected guidance'], 'cause': 'unknown', 'ownership': 'unknown',
            'missingProof': 'Independent execution missing', 'mechanism': 'Potential shared point-of-use gap', 'supportedScope': 'Two synthetic observations',
            'consumerEffects': 'unknown beyond scoped inputs', 'pointOfUseAction': 'Name available next action',
            'relationships': [{'requestId': r['requestId'], 'repairId': 'repair-proposed-one', 'groupId': None, 'explanation': 'Same supported mechanism'} for r in references],
            'proposedDisposition': 'needs-proof', 'rationale': 'Workaround plausibility is not qualification', 'correlation': {'availability': 'pending'}}
        before = (self.owner / 'docs/owner-ledger.json').read_bytes()
        from jsonschema import Draft202012Validator
        Draft202012Validator(build_repair_contract.build()['assessment.schema.json']).validate(assessment)
        outcome = evaluator.submit(self.owner, assessment)
        self.assertTrue(Path(outcome['queuedAssessment']).is_file())
        self.assertEqual(before, (self.owner / 'docs/owner-ledger.json').read_bytes())
        self.assertEqual(outcome['assessmentSha256'], evaluator.submit(self.owner, assessment)['assessmentSha256'])
        assessment['requests'][0]['selectedKnowledgeVersion'] = 'new-unavailable-version'
        with self.assertRaisesRegex(ValueError, 'version-mismatch'): evaluator.submit(self.owner, assessment)

    def test_historical_unknown_contract_preserved_as_bytes_without_new_answers(self):
        historical = deepcopy(self.value)
        historical['contractVersion'] = '0.9'
        historical['unclassified'] = ['old vocabulary never rewritten']
        source = self.root / 'historical.json'
        source.write_text(json.dumps(historical, separators=(',', ':')), encoding='utf-8')
        raw = source.read_bytes()
        result = evaluator.preserve_original(self.owner, source, 'maintenance')
        queued = self.owner / rf.QUEUE / historical['requestId'] / '1/packet/request.json'
        self.assertEqual(raw, queued.read_bytes())
        self.assertEqual(c.sha(raw), result['requestSha256'])
        self.assertEqual('knowledge-old', result['selectedKnowledgeVersion'])
        with self.assertRaisesRegex(ValueError, 'unsupported-contract'): c.request(json.loads(queued.read_bytes()))

    def test_delivery_lock_blocks_concurrent_public_sessions_and_releases(self):
        rf.configure(self.consumer, 'consumer')
        with rf.delivery_lock(self.consumer):
            with self.assertRaises(OSError):
                with rf.delivery_lock(self.consumer): pass
        with rf.delivery_lock(self.consumer): pass

    def test_recover_lost_index_and_link_known_implementation_and_release_objects(self):
        rf.configure(self.consumer, 'consumer')
        api = RecordingGitHub()
        body = rf.marker(self.value) + '\nproject `synthetic-project`\nAdditional original evidence'
        api.comments[7] = [{'body': body}]
        objects = [{'repository': c.UPSTREAM, 'kind': 'issue', 'number': 7}]
        recovered = rf.recover(self.consumer, api, 'synthetic-project', objects)
        self.assertEqual(self.value['requestId'], recovered['references'][0]['requestId'])
        self.assertNotIn('receipt', recovered['references'][0])
        rf.link(self.consumer, self.value['requestId'], [{'repository': c.UPSTREAM, 'kind': 'implementation-pr', 'number': 8},
                                                       {'repository': c.UPSTREAM, 'kind': 'release', 'number': 9}])
        records = rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']
        self.assertEqual(2, len(records))
        self.assertFalse(any('status' in record for record in records))
        result = rf.status(records, api)
        self.assertEqual(3, len(result['sources']))
        self.assertEqual([], api.writes)

    def guardian_api(self, bad=None):
        prefix = f"requests/{self.value['requestId']}/r1"
        files = c.inventory(self.packet)
        blobs = {}
        tree = []
        changes = []
        for name, data in files.items():
            sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            blobs[sha] = {'encoding': 'base64', 'size': len(data), 'content': base64.b64encode(data).decode()}
            tree.append({'path': prefix + '/' + name, 'type': 'blob', 'mode': '100644', 'size': len(data), 'sha': sha})
            changes.append({'filename': prefix + '/' + name, 'status': 'added'})
        if bad == 'policy': changes[0]['filename'] = '.github/workflows/guardian.yml'
        if bad == 'prior-evidence': changes[0]['status'] = 'modified'
        if bad == 'symlink': tree[0]['mode'] = '120000'
        if bad == 'extra-tree': tree.append(dict(tree[0], path=prefix + '/evidence/extra.txt'))
        if bad == 'truncated': pass
        def api(endpoint):
            if '/pulls/' in endpoint and '/files?' not in endpoint:
                return {'head': {'sha': HEAD}, 'base': {'sha': BASE, 'ref': 'main', 'repo': {'full_name': c.EVIDENCE}}, 'changed_files': len(changes)}
            if '/files?' in endpoint: return changes
            if '/git/commits/' in endpoint: return {'parents': [{'sha': 'd' * 40 if bad in ('ancestor', 'diverged') else BASE}]}
            if '/compare/' in endpoint: return {'status': 'ahead', 'merge_base_commit': {'sha': 'd' * 40 if bad == 'ancestor' else 'e' * 40}}
            if '/git/trees/' in endpoint: return {'tree': tree, 'truncated': bad == 'truncated'}
            if '/git/blobs/' in endpoint: return blobs[endpoint.rsplit('/', 1)[-1]]
            raise AssertionError(endpoint)
        return api

    def test_trusted_guardian_exact_head_bound_data_only_and_adversarial_inventory(self):
        # repro.py raises if executed: passing proves the guardian only inspected bytes.
        with patch.object(subprocess, 'run', side_effect=AssertionError('guardian executed a subprocess')):
            proof = guardian.inspect(self.guardian_api(), c.EVIDENCE, 1, HEAD, BASE, TRUSTED)
        self.assertEqual(HEAD, proof['submittedCommit']); self.assertEqual(TRUSTED, proof['validatorCommit'])
        for bad in ('policy', 'prior-evidence', 'symlink', 'extra-tree', 'truncated', 'diverged'):
            with self.subTest(bad=bad), self.assertRaises(ValueError): guardian.inspect(self.guardian_api(bad), c.EVIDENCE, 1, HEAD, BASE, TRUSTED)
        with self.assertRaises(ValueError): guardian.inspect(self.guardian_api(), 'consumer/default-remote', 1, HEAD, BASE, TRUSTED)

    def test_dedicated_app_check_binds_actual_head_and_never_passes_rejected_or_moved_data(self):
        for bad in (None, 'policy', 'symlink', 'moved', 'ancestor'):
            reads, writes = self.guardian_api(bad), []
            count = 0
            def api(method, endpoint, payload=None):
                nonlocal count
                if method != 'GET':
                    writes.append((method, endpoint, payload))
                    return {'id': 9}
                result = reads(endpoint)
                if '/pulls/1' == endpoint[-8:]:
                    count += 1
                    result['state'] = 'open'
                    if bad == 'moved' and count >= 3:
                        result['head']['sha'] = 'd' * 40
                return result
            proof = guardian_check.run(api, c.EVIDENCE, 1, TRUSTED)
            self.assertEqual(HEAD, writes[0][2]['head_sha'])
            self.assertEqual(guardian_check.CHECK, writes[0][2]['name'])
            self.assertEqual('success' if bad in (None, 'ancestor') else 'failure', writes[-1][2]['conclusion'])
            self.assertEqual(bad in (None, 'ancestor'), proof is not None)
            self.assertIn(TRUSTED, writes[-1][2]['output']['summary'])
        with self.assertRaises(ValueError): guardian_check.run(api, 'other/repo', 1, TRUSTED)

    def test_effective_rules_required_and_app_write_failure_cannot_become_success(self):
        rf.configure(self.consumer, 'consumer'); api = RecordingGitHub(); review = self.review()
        original = api.handle
        api.handle = lambda method, endpoint, payload: [] if '/rules/branches/main?' in endpoint else original(method, endpoint, payload)
        with self.assertRaises(ValueError): rf.public(self.consumer, self.packet, review, review['reviewDigest'], api)
        self.assertEqual([], api.writes)
        reads = self.guardian_api()
        def unavailable(method, endpoint, payload=None):
            if method != 'GET': raise OSError('check API unavailable')
            return dict(reads(endpoint), state='open')
        with self.assertRaises(OSError): guardian_check.run(unavailable, c.EVIDENCE, 1, TRUSTED)

    def test_prepared_repository_is_source_only_and_internal_evaluator_not_packaged(self):
        from build_release import BUNDLE_SOURCE_PREFIXES, BUNDLE_RUNTIME_SCRIPTS, deterministic_zip
        output = prepare_evidence_repository.prepare(self.root / 'evidence-source')
        self.assertIsNone(rf.read(output / 'guardian-deployment.json')['validatorCommit'])
        self.assertEqual((ROOT / 'extensions/program-kit-governance/scripts/repair_contract.py').read_bytes(), (output / 'repair_contract.py').read_bytes())
        workflow = (output / '.github/workflows/guardian.yml').read_text()
        self.assertIn('vars.GUARDIAN_VALIDATOR_COMMIT', workflow)
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn('environment: evidence-guardian', workflow)
        self.assertIn('permission-checks: write', workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertNotIn('head.sha }}\n          persist', workflow)
        self.assertTrue(all(not x.startswith('.agents/') for x in (*BUNDLE_SOURCE_PREFIXES, *BUNDLE_RUNTIME_SCRIPTS)))
        import zipfile
        archive = self.root / 'governance.zip'
        deterministic_zip(ROOT / 'extensions/program-kit-governance', archive)
        with zipfile.ZipFile(archive) as zipped:
            self.assertIn('scripts/repair_feedback.py', zipped.namelist())
            self.assertIn('commands/speckit.program-kit-governance.repair-request.md', zipped.namelist())
            self.assertFalse(any('repair-evaluator' in x for x in zipped.namelist()))


# Separate fixture setup keeps these scenarios in the same declared validator.
class IntakeTests(unittest.TestCase):
    setUp = RepairTests.setUp

    def test_cli_missing_owner_identifies_required_registration(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/repair_evaluator.py'), '--root', str(self.owner),
                                 'register-owner', '--ledger', 'docs/owner-ledger.json'], capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertIn('PKRF owner-required-register-and-configure-route', result.stderr)
        self.assertEqual('', result.stdout)

    def queue(self, packets=None):
        rf.configure(self.consumer, 'contributor', self.owner, 'maintenance')
        for directory, _ in packets or [(self.packet, self.value)]:
            rf.local(self.consumer, directory, 'docs/owner-ledger.json')

    def test_owner_binding_missing_delivery_cross_owner_and_changed_route_fail(self):
        with self.assertRaisesRegex(ValueError, 'owner-required'):
            rf.configure(self.consumer, 'contributor', self.owner)
        self.queue()
        value = assessment(self.owner, [(self.packet, self.value)])
        with self.assertRaisesRegex(ValueError, 'selected-owner-ledger'):
            rf.local(self.consumer, self.packet, 'extensions/program-kit-governance/extension.yml')
        rf.write(self.owner / 'docs/other.json', {'items': []})
        evaluator.register_owner(self.owner, 'other', 'docs/other.json')
        second, other = packet(self.root, suffix='other-owner-packet')
        rf.configure(self.consumer, 'contributor', self.owner, 'other')
        rf.local(self.consumer, second, 'docs/other.json')
        mixed = assessment(self.owner, [(self.packet, self.value), (second, other)])
        with self.assertRaisesRegex(ValueError, 'delivery-owner'):
            evaluator.submit(self.owner, mixed)
        directory = intake.directory(self.owner, self.value['requestId'], 1)
        delivery = (directory / 'delivery.json').read_bytes()
        (directory / 'delivery.json').unlink()
        with self.assertRaises(ValueError): evaluator.submit(self.owner, value)
        self.assertEqual('invalid-or-unrouted', evaluator.inbox(self.owner, 'maintenance')['records'][0]['availability'])
        (directory / 'delivery.json').write_bytes(delivery)
        rf.write(intake.owner_path(self.owner, 'maintenance'), {'routeVersion': 1, 'ownerId': 'maintenance', 'ledger': 'docs/other.json', 'adapter': 'items-v1'})
        with self.assertRaisesRegex(ValueError, 'owner-route-changed'):
            evaluator.submit(self.owner, value)

    def test_current_packet_revalidated_and_historical_accounts_remain_unqualified(self):
        self.queue()
        value = assessment(self.owner, [(self.packet, self.value)])
        queued = intake.directory(self.owner, self.value['requestId'], 1) / 'packet'
        (queued / 'report.md').write_bytes(b'Changed synthetic proof')
        with self.assertRaisesRegex(ValueError, 'member-identity'): evaluator.submit(self.owner, value)
        for record in evaluator.inbox(self.owner, 'maintenance')['records']:
            self.assertEqual('invalid-or-unrouted', record['availability'])
        historical = deepcopy(self.value)
        historical.update(requestId='rf-' + '0' * 32, contractVersion='0.9')
        source = self.root / 'historical.json'; rf.write(source, historical)
        evaluator.preserve_original(self.owner, source, 'maintenance')
        preserved = intake.directory(self.owner, historical['requestId'], 1) / 'packet'
        old_assessment = assessment(self.owner, [(preserved, historical)], 'historical')
        evaluator.submit(self.owner, old_assessment)
        data = intake.state(self.owner, old_assessment['ownerRoute'], old_assessment['requests'][0])
        self.assertEqual('historical-unqualified', data['qualification'])
        self.assertEqual(source.read_bytes(), (preserved / 'request.json').read_bytes())
        old_assessment['assessmentVersion'] = '1.0'; old_assessment.pop('ownerRoute')
        old_assessment['relationships'][0]['repairId'] = 'repair-historical'
        with self.assertRaisesRegex(ValueError, 'historical-assessment-read-only'): evaluator.submit(self.owner, old_assessment)

    def test_owner_dispositions_are_request_scoped_fresh_and_proof_bound(self):
        second = packet(self.root, suffix='second')
        self.queue([(self.packet, self.value), second])
        one, two = assessment(self.owner, [(self.packet, self.value)], 'one'), assessment(self.owner, [second], 'two')
        for value in (one, two): evaluator.submit(self.owner, value)
        owner_decision(self.owner, one, facts={'implemented': {'value': True, 'proof': ['Synthetic changed source and owner record']}})
        owner_decision(self.owner, two, 'reject')
        records = rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']
        first, other = rf.status([records[0]]), rf.status([records[1]])
        self.assertTrue(first['lifecycle']['implemented'])
        self.assertEqual('reject', other['sources'][0]['data']['ownerDecision']['disposition'])
        self.assertEqual('unknown', other['lifecycle']['implemented'])
        self.assertEqual('unknown', first['lifecycle']['released'])
        self.assertNotIn('items', first['sources'][0]['data'])
        self.assertEqual(2, len(evaluator.inbox(self.owner, 'maintenance')['records']))
        page = evaluator.inbox(self.owner, 'maintenance', limit=1)
        self.assertEqual(1, len(evaluator.inbox(self.owner, 'maintenance', limit=1, after=page['next'])['records']))
        ledger_path = self.owner / 'docs/owner-ledger.json'; ledger = rf.read(ledger_path)
        self.assertEqual('Synthetic existing approval preserved', ledger['approval'])
        ledger['repairFeedback']['decisions'][0]['facts']['implemented']['value'] = False
        rf.write(ledger_path, ledger)
        self.assertFalse(rf.status([records[0]])['lifecycle']['implemented'])
        ledger['repairFeedback']['decisions'][0]['facts']['implemented']['proof'] = []
        rf.write(ledger_path, ledger)
        self.assertEqual('unavailable', rf.status([records[0]])['sources'][0]['availability'])
        self.assertEqual('unknown', rf.status([records[0]])['lifecycle']['implemented'])
        self.assertNotIn('implemented', (self.consumer / rf.PERSONAL / 'submissions.json').read_text())

    def test_correlation_followup_is_append_only_and_retry_idempotent(self):
        self.queue()
        folder = intake.directory(self.owner, self.value['requestId'], 1)
        before = (folder / 'delivery.json').read_bytes()
        for _ in range(2): rf.local(self.consumer, self.packet, 'docs/owner-ledger.json', correlation())
        self.assertEqual(before, (folder / 'delivery.json').read_bytes())
        self.assertEqual(1, len(list((folder / 'correlation').glob('*.json'))))
        self.assertEqual(1, len(rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']))

    def test_legacy_binding_preserves_delivery_and_refreshes_reference_only_index(self):
        self.queue()
        folder = intake.directory(self.owner, self.value['requestId'], 1)
        current = rf.read(folder / 'delivery.json')
        legacy = {k: v for k, v in current.items() if k not in ('ownerRoute', 'source')}
        legacy['correlation'] = {'availability': 'pending'}
        rf.write(folder / 'delivery.json', legacy)
        original = (folder / 'delivery.json').read_bytes()
        index_path = self.consumer / rf.PERSONAL / 'submissions.json'
        index = rf.read(index_path)
        for record in index['requests']:
            record.pop('ownerRoute'); record.pop('checkout')
        rf.write(index_path, index)
        self.assertEqual('unavailable', rf.status(index['requests'])['sources'][0]['availability'])
        with self.assertRaises(ValueError): evaluator.submit(self.owner, assessment(self.owner, [(self.packet, self.value)]))
        evaluator.bind_legacy(self.owner, 'maintenance', current)
        rf.local(self.consumer, self.packet, 'docs/owner-ledger.json')
        self.assertEqual(original, (folder / 'delivery.json').read_bytes())
        self.assertEqual('available', rf.status(rf.read(index_path)['requests'])['sources'][0]['availability'])

    def test_changed_assessment_unknown_finding_and_ambiguous_owner_decision_unavailable(self):
        self.queue()
        value = assessment(self.owner, [(self.packet, self.value)])
        evaluator.submit(self.owner, value)
        owner_decision(self.owner, value)
        ledger_path = self.owner / 'docs/owner-ledger.json'
        original = rf.read(ledger_path)
        for mode in ('missing-finding', 'ambiguous', 'changed-assessment', 'missing-ledger'):
            with self.subTest(mode=mode):
                ledger = deepcopy(original)
                if mode == 'missing-finding': ledger['repairFeedback']['decisions'][0]['repairIds'] = ['unrelated']
                if mode == 'ambiguous': ledger['repairFeedback']['decisions'].append(deepcopy(ledger['repairFeedback']['decisions'][0]))
                rf.write(ledger_path, ledger)
                assessment_path = self.owner / intake.BASE / 'assessments/assess-synthetic.json'
                raw = assessment_path.read_bytes()
                if mode == 'changed-assessment': assessment_path.write_bytes(raw + b' ')
                if mode == 'missing-ledger': ledger_path.unlink()
                records = rf.read(self.consumer / rf.PERSONAL / 'submissions.json')['requests']
                state = rf.status(records)
                self.assertEqual('unavailable', state['sources'][0]['availability'])
                self.assertEqual('unknown', state['lifecycle']['implemented'])
                assessment_path.write_bytes(raw)
                rf.write(ledger_path, original)

    def public_api(self, accepted=False, bad=None):
        fake, reads = RecordingGitHub(), RepairTests.guardian_api(self)
        original = fake.handle
        marker = f"<!-- program-kit-repair {self.value['requestId']} revision=1 sha256={c.sha((self.packet / 'request.json').read_bytes())} -->"
        merge = 'e' * 40
        def handle(method, endpoint, payload):
            if '/pulls/1' in endpoint:
                obj = reads(endpoint)
                if '/files?' not in endpoint:
                    obj.update(merged=accepted, merge_commit_sha=merge, state='closed' if accepted else 'open')
                    if bad == 'moved': obj['head']['sha'] = 'f' * 40
                return obj
            if '/git/' in endpoint:
                if merge in endpoint:
                    result = reads(endpoint.replace(merge, HEAD))
                    if bad == 'accepted-bytes': result['tree'] = []
                    return result
                return reads(endpoint)
            if '/compare/' in endpoint: return {'status': 'ahead', 'merge_base_commit': {'sha': merge}}
            if '/check-runs?' in endpoint:
                return {'total_count': 1, 'check_runs': [{'id': 9, 'name': 'program-kit-evidence/guardian', 'app': {'id': 15368 if bad == 'lookalike' else 123},
                    'head_sha': HEAD, 'conclusion': 'success', 'output': {'summary': json.dumps({'submittedCommit': HEAD,
                    'validatorCommit': TRUSTED, 'contractVersion': c.VERSION, 'guardianVersion': c.GUARDIAN})}}]}
            if endpoint == f'repos/{c.UPSTREAM}/issues/7': return {'body': 'wrong' if bad == 'marker' else marker}
            return original(method, endpoint, payload)
        fake.handle = handle
        return fake

    def test_public_pinned_import_full_packet_retry_and_acceptance_separation(self):
        fake = self.public_api()
        imported = evaluator.import_public(self.owner, 'maintenance', 1, HEAD, BASE, TRUSTED, 7, fake)
        self.assertFalse(imported['observation']['evidenceAccepted'])
        folder = intake.directory(self.owner, self.value['requestId'], 1)
        self.assertEqual(c.inventory(self.packet), c.inventory(folder / 'packet'))
        before = (folder / 'delivery.json').read_bytes()
        fake = self.public_api(accepted=True)
        accepted = evaluator.import_public(self.owner, 'maintenance', 1, HEAD, BASE, TRUSTED, 7, fake)
        self.assertTrue(accepted['observation']['evidenceAccepted'])
        self.assertEqual([], fake.writes)
        self.assertEqual(before, (folder / 'delivery.json').read_bytes())
        self.assertEqual(2, len(list((folder / 'public-observations').glob('*.json'))))
        value = assessment(self.owner, [(self.packet, self.value)])
        evaluator.submit(self.owner, value)
        self.assertIsNone(intake.state(self.owner, value['ownerRoute'], value['requests'][0])['ownerDecision'])

    def test_public_wrong_marker_moved_head_and_same_name_app_do_not_accept(self):
        for bad in ('marker', 'moved', 'accepted-bytes'):
            with self.assertRaises(ValueError): evaluator.import_public(self.owner, 'maintenance', 1, HEAD, BASE, TRUSTED, 7, self.public_api(True, bad))
        outcome = evaluator.import_public(self.owner, 'maintenance', 1, HEAD, BASE, TRUSTED, 7, self.public_api(True, 'lookalike'))
        self.assertFalse(outcome['observation']['evidenceAccepted'])


class InstalledRepairTests(unittest.TestCase):
    def test_native_command_skill_and_upgrade_preserve_personal_and_original_profile(self):
        temporary = tempfile.TemporaryDirectory(prefix='rf-native-')
        owner_temporary = tempfile.TemporaryDirectory(prefix='rf-owner-')
        owner = init(Path(owner_temporary.name) / 'owner', contributor=True)
        consumer = Path(temporary.name)
        old = os.environ.get('SPECIFY_INIT_DIR')
        os.environ['SPECIFY_INIT_DIR'] = str(consumer)
        import specify_cli
        cli = [sys.executable, str(ROOT / 'scripts/invoke_specify.py'), '--site-packages',
               str(Path(specify_cli.__file__).parent.parent), '--']
        def invoke(arguments):
            result = subprocess.run(cli + arguments, cwd=consumer, capture_output=True, text=True, encoding='utf-8', timeout=180)
            logs = ROOT / 'artifacts/tests/repair-feedback'; logs.mkdir(parents=True, exist_ok=True)
            (logs / ('native-' + str(len(list(logs.glob('native-*.log')))) + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        try:
            invoke(['init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py', '--ignore-agent-tools'])
            invoke(['extension', 'add', str(ROOT / 'extensions/program-kit-governance'), '--dev'])
            subprocess.run(['git', 'init', '-q', str(consumer)], check=True, capture_output=True)
            self.assertTrue((consumer / '.agents/skills/speckit-program-kit-governance-repair-request/SKILL.md').is_file())
            installed = consumer / '.specify/extensions/program-kit-governance'
            self.assertEqual((ROOT / 'extensions/program-kit-governance/scripts/repair_feedback.py').read_bytes(), (installed / 'scripts/repair_feedback.py').read_bytes())
            rf.configure(consumer, 'consumer')
            personal = {p.name: p.read_bytes() for p in (consumer / rf.PERSONAL).iterdir()}
            (consumer / 'retained-profile.json').write_text('{"selected":"old-profile"}', encoding='utf-8')
            invoke(['extension', 'add', str(ROOT / 'extensions/program-kit-governance'), '--dev', '--force'])
            invoke(['integration', 'use', 'codex'])
            self.assertEqual(personal, {p.name: p.read_bytes() for p in (consumer / rf.PERSONAL).iterdir()})
            self.assertFalse((consumer / '.agents/skills/program-kit-repair-evaluator').exists())
            self.assertEqual('{"selected":"old-profile"}', (consumer / 'retained-profile.json').read_text())
            result = subprocess.run([sys.executable, str(installed / 'scripts/repair_feedback.py'), '--root', str(consumer), 'draft',
                                     '--project', 'installed-synthetic', '--title', 'Native reporter', '--output', str(consumer / 'draft.json')], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(c.VERSION, rf.read(consumer / 'draft.json')['contractVersion'])
            # Exercise the installed CLI through a complete owner handoff. The
            # fixture owns this ledger; no active maintenance checkout is used.
            def reporter(arguments):
                result = subprocess.run([sys.executable, str(installed / 'scripts/repair_feedback.py'), '--root', str(consumer), *arguments],
                                        capture_output=True, text=True, encoding='utf-8', timeout=60)
                self.assertEqual(0, result.returncode, result.stderr)
                return json.loads(result.stdout)
            selected, observation = packet(Path(owner_temporary.name))
            reporter(['configure', '--mode', 'contributor', '--checkout', str(owner), '--owner', 'maintenance'])
            reporter(['local', '--packet', str(selected), '--ledger', 'docs/owner-ledger.json'])
            value = assessment(owner, [(selected, observation)], 'installed')
            evaluator.submit(owner, value)
            owner_decision(owner, value, 'adopt', {'implemented': {'value': True, 'proof': ['Synthetic owner source record']}})
            state = reporter(['status', '--request-id', observation['requestId']])
            self.assertTrue(state['lifecycle']['assessed'])
            self.assertTrue(state['lifecycle']['implemented'])
            self.assertEqual('unknown', state['lifecycle']['released'])
            self.assertEqual('U0', state['sources'][0]['data']['ownerDecision']['repairIds'][0])
            personal = {p.name: p.read_bytes() for p in (consumer / rf.PERSONAL).iterdir()}
            invoke(['extension', 'add', str(ROOT / 'extensions/program-kit-governance'), '--dev', '--force'])
            invoke(['integration', 'use', 'codex'])
            self.assertEqual(personal, {p.name: p.read_bytes() for p in (consumer / rf.PERSONAL).iterdir()})
            self.assertTrue(reporter(['status', '--request-id', observation['requestId']])['lifecycle']['implemented'])
            import native_phase_ownership
            native_phase_ownership.preflight(consumer, ROOT)
        finally:
            if old is None: os.environ.pop('SPECIFY_INIT_DIR', None)
            else: os.environ['SPECIFY_INIT_DIR'] = old
            temporary.cleanup()
            owner_temporary.cleanup()


if __name__ == '__main__':
    unittest.main()
