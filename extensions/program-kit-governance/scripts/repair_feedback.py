"""Portable local repair reporting and reviewed, resumable GitHub delivery.

GitHub calls are injected in tests. No subprocess executes evidence or repros.
Personal state stores references and historical receipts, never current status.
"""
from __future__ import annotations
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import quote

import repair_contract as c

PERSONAL = '.program-kit/repair-feedback-personal'
QUEUE = 'artifacts/repair-feedback/intake'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path, default=None):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).is_file() else default


def write(path, value, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = c.encoded(value)
    if immutable and path.exists():
        c.require(path.read_bytes() == data, 'immutable-record-conflict')
        return
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def git(root, *args):
    result = subprocess.run(['git', '-c', 'safe.directory=' + str(Path(root).resolve()),
                             '-c', 'core.excludesFile=' + ('' if os.name == 'nt' else '/dev/null'),
                             '-C', str(root), *args], capture_output=True, timeout=30)
    c.require(result.returncode == 0, 'git-operation-failed')
    return result.stdout.decode('utf-8').strip()


def checkout(root):
    c.require(root is not None, 'contributor-checkout-must-be-user-selected')
    root = Path(root).resolve()
    # Git normalizes Windows extended paths differently from pathlib. Compare
    # actual directory identity, so a valid selected root is not rejected due
    # to spelling while a nested or unrelated repository still fails.
    c.require(os.path.samefile(Path(git(root, 'rev-parse', '--show-toplevel')).resolve(), root), 'checkout-root-required')
    c.require((root / 'extensions/program-kit-governance/extension.yml').is_file() and
              (root / '.agents/skills/program-kit-repair-evaluator/SKILL.md').is_file(), 'program-kit-contributor-checkout-required')
    return root


def configure(root, mode, contributor=None):
    c.require(mode in ('consumer', 'contributor'), 'mode')
    selected = str(checkout(contributor)) if mode == 'contributor' else None
    directory = c.inside(root, PERSONAL)
    # Git's own exclude file is local, upgrade-preserved and outside input digests.
    exclude = Path(git(root, 'rev-parse', '--git-path', 'info/exclude'))
    if not exclude.is_absolute():
        exclude = Path(root) / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    previous = exclude.read_text(encoding='utf-8') if exclude.exists() else ''
    rule = '/' + PERSONAL + '/'
    if rule not in previous.splitlines():
        with exclude.open('a', encoding='utf-8') as stream:
            stream.write('\n' + rule + '\n')
    probe = PERSONAL + '/preferences.json'
    c.require(git(root, 'check-ignore', '--no-index', '--', probe) == probe, 'personal-ignore-not-proven')
    c.require(not git(root, 'ls-files', '--', PERSONAL), 'personal-records-already-tracked-remove-from-index-first')
    write(directory / 'preferences.json', {'schemaVersion': 1, 'mode': mode, 'checkout': selected})
    if not (directory / 'submissions.json').exists():
        write(directory / 'submissions.json', {'schemaVersion': 1, 'requests': []})
    return {'disclosure': 'Created or updated ignored personal preferences and submission index; choices survive upgrades. No credentials or current status stored.',
            'path': str(directory), 'mode': mode, 'checkout': selected, 'ignoreVerified': True}


def personal(root):
    directory = c.inside(root, PERSONAL)
    value = read(directory / 'preferences.json')
    c.require(value is not None, 'first-use-ask-contributor-default-consumer-then-configure')
    c.require(git(root, 'check-ignore', '--no-index', '--', PERSONAL + '/preferences.json') == PERSONAL + '/preferences.json', 'personal-ignore-not-proven')
    return directory, value


def remember(root, value):
    directory, _ = personal(root)
    index = read(directory / 'submissions.json', {'schemaVersion': 1, 'requests': []})
    # Append historical reference records; never overwrite implementation status.
    allowed = {'requestId', 'projectId', 'revision', 'requestSha256', 'route', 'queue', 'ledger', 'objects', 'receipt', 'account', 'host'}
    c.require(set(value) <= allowed, 'submission-index-reference-fields-only')
    for obj in value.get('objects', []):
        c.fields(obj, ('repository', 'kind', 'number'))
        c.require(obj['repository'] in (c.UPSTREAM, c.EVIDENCE) and obj['kind'] in ('issue', 'evidence-pr', 'implementation-pr', 'release')
                  and type(obj['number']) is int and obj['number'] > 0, 'index-object-reference')
    if 'receipt' in value:
        c.fields(value['receipt'], ('deliveredAt', 'reviewDigest', 'issue', 'evidencePR', 'commit'))
    if value not in index['requests']:
        index['requests'].append(value)
        write(directory / 'submissions.json', index)


def draft(project_id, title, component='unclassified', previous=None, previous_sha=None):
    if previous is not None:
        c.request(previous)
    return {'contractVersion': c.VERSION, 'requestId': previous['requestId'] if previous else 'rf-' + uuid.uuid4().hex,
            'revision': previous['revision'] + 1 if previous else 1,
            'supersedes': (previous_sha or c.sha(c.encoded(previous))) if previous else None,
            'projectId': project_id, 'createdAt': now(), 'component': component, 'title': title,
            'originalAccount': previous['originalAccount'] if previous else 'unknown',
            'diagnostics': {section: {'answer': 'unknown', 'evidenceClass': 'unknown', 'explanationKind': 'unknown',
                                     'references': []} for section in c.SECTIONS},
            'unclassified': [], 'evidence': {key: 'unknown' for key in
                ('programKitVersion', 'profileVersion', 'knowledgeVersion', 'sourceCommit', 'dirtyState')} | {'members': []},
            'omissions': []}


def prepare(source, output):
    """Seal already selected/sanitized evidence. Preserve originals; never truncate."""
    source, output = Path(source), Path(output)
    c.require(not output.exists(), 'output-must-be-new')
    files = c.inventory(source)
    c.require('request.json' in files and 'report.md' in files, 'request-and-report-required')
    value = c.request(json.loads(files['request.json']))
    # Callers declare purpose/provenance/transforms; the sealer fills measured identity only.
    members = {m['path']: m for m in value['evidence']['members']}
    c.require(set(files) == {'request.json', *members}, 'declare-each-evidence-member-first')
    for name in members:
        members[name]['bytes'] = len(files[name])
        members[name]['sha256'] = c.sha(files[name])
    files['request.json'] = c.encoded(value)
    with tempfile.TemporaryDirectory(prefix='repair-seal-') as temporary:
        for name, data in files.items():
            target = c.inside(temporary, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        proof = c.guard(temporary)
        shutil.copytree(temporary, output)
    return proof


def local(root, packet, ledger, correlation=None):
    _, preferences = personal(root)
    c.require(preferences['mode'] == 'contributor', 'local-route-requires-selected-contributor-checkout')
    target = checkout(preferences['checkout'])
    proof = c.guard(packet)
    value = read(Path(packet) / 'request.json')
    c.safe_name(ledger)
    c.require(c.inside(target, ledger).is_file(), 'owner-ledger-must-exist')
    relative = QUEUE + '/' + value['requestId'] + '/' + str(value['revision'])
    if value['revision'] > 1:
        previous = c.inside(target, QUEUE + '/' + value['requestId'] + '/' + str(value['revision'] - 1) + '/packet/request.json')
        c.require(previous.is_file() and c.sha(previous.read_bytes()) == value['supersedes'], 'queued-predecessor-required')
    directory = c.inside(target, relative)
    # Durable packet first, immutable delivery record last. A retry repairs incomplete copies.
    for name, data in c.inventory(packet).items():
        path = c.inside(directory / 'packet', name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            c.require(path.read_bytes() == data, 'queued-revision-conflict')
        else:
            with path.open('xb') as stream:
                stream.write(data)
    record = {'requestId': value['requestId'], 'revision': value['revision'], 'requestSha256': proof['requestSha256'],
              'ledger': ledger, 'correlation': correlation or {'availability': 'pending', 'reason': 'not-retrieved'},
              'meaning': 'queued observation; owner disposition required'}
    write(directory / 'delivery.json', record, immutable=True)
    remember(root, {'requestId': value['requestId'], 'projectId': value['projectId'], 'revision': value['revision'],
                    'requestSha256': proof['requestSha256'], 'route': 'local', 'queue': str(directory),
                    'ledger': str(c.inside(target, ledger))})
    return record


class GitHub:
    def __init__(self, executable=None, host='github.com'):
        c.require(host == 'github.com', 'v1-supported-host-github.com')
        self.executable = executable or shutil.which('gh')
        if not self.executable:
            known = [Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'GitHub CLI/gh.exe',
                     Path('/opt/homebrew/bin/gh'), Path('/usr/local/bin/gh'), Path('/usr/bin/gh')]
            c.require(not any(p.is_file() for p in known), 'github-cli-outside-PATH-add-install-directory')
            raise ValueError('PKRF github-cli-absent-see-https://cli.github.com/')
        self.host = host

    def auth(self):
        result = subprocess.run([self.executable, 'auth', 'status', '--hostname', self.host], capture_output=True, timeout=30)
        c.require(result.returncode == 0, 'github-auth-unavailable-run-gh-auth-login-yourself')
        return self.api('GET', 'user')['login']

    def api(self, method, endpoint, payload=None):
        c.require(not endpoint.startswith(('http', '/')) and
                  '..' not in endpoint.split('?', 1)[0].split('/'), 'github-endpoint')
        command = [self.executable, 'api', '--hostname', self.host, '--method', method,
                   '-H', 'Cache-Control: no-cache, no-store', '-H', 'Pragma: no-cache', endpoint]
        data = None
        if payload is not None:
            command += ['--input', '-']
            data = json.dumps(payload)
        # Deliberately no --cache; suppress raw stderr which may contain submitted content.
        result = subprocess.run(command, input=data, capture_output=True, text=True, encoding='utf-8', timeout=60)
        c.require(result.returncode == 0, 'github-retrieval-or-mutation-unavailable-reconcile-before-retry')
        return json.loads(result.stdout) if result.stdout.strip() else None


def pages(api, endpoint, limit=100):
    rows = []
    for page in range(1, limit + 1):
        batch = api.api('GET', endpoint + ('&' if '?' in endpoint else '?') + f'per_page=100&page={page}')
        c.require(isinstance(batch, list), 'paginated-response')
        rows.extend(batch)
        if len(batch) < 100:
            return rows
    raise ValueError('PKRF pagination-incomplete')


def search(api, terms, alternate, refine=None):
    c.require(1 <= len(terms) <= 120 and 1 <= len(alternate) <= 120, 'bounded-search-terms')
    queries, candidates = [], {}
    complete = True
    for state in ('open', 'closed'):
        current = terms
        for attempt in range(3):
            query = f'repo:{c.UPSTREAM} is:issue state:{state} {current}'
            result = api.api('GET', 'search/issues?q=' + quote(query, safe='') + '&per_page=10')
            queries.append({'query': query, 'bound': 10, 'total': result['total_count'], 'incomplete': result.get('incomplete_results', False)})
            if result['total_count'] == 0 and attempt == 0:
                current = alternate
                continue
            if result['total_count'] > 10 and refine and current != refine:
                current = refine
                continue
            complete &= not result.get('incomplete_results', False) and result['total_count'] <= 10
            for item in result['items'][:10]:
                number = item['number']
                if number not in candidates and len(candidates) < 20:
                    candidates[number] = {'issue': api.api('GET', f'repos/{c.UPSTREAM}/issues/{number}'),
                                          'comments': pages(api, f'repos/{c.UPSTREAM}/issues/{number}/comments')}
            break
    return {'retrievedAt': now(), 'complete': bool(complete), 'queries': queries, 'candidates': list(candidates.values()),
            'meaning': 'bounded correlation; empty results do not prove no duplicate'}


def marker(value):
    return f"<!-- program-kit-repair {value['requestId']} revision={value['revision']} sha256={c.sha(c.encoded(value))} -->"


def plan(packet, correlation, destination, rationale, account, base_commit, validator_commit):
    proof = c.guard(packet)
    value = read(Path(packet) / 'request.json')
    c.require(correlation.get('complete') is True and correlation.get('queries'), 'duplicate-check-incomplete-public-paused')
    c.require(destination == 'new' or (type(destination) is int and any(
        row['issue']['number'] == destination for row in correlation['candidates'])), 'destination-must-be-inspected-or-new')
    c.require(re.fullmatch(r'[A-Za-z0-9-]+', account) and re.fullmatch(r'[0-9a-f]{40}', base_commit)
              and re.fullmatch(r'[0-9a-f]{40}', validator_commit), 'public-account-and-pinned-repository-commits')
    c.text(rationale)
    tag = marker(value)
    branch = f"repair/{value['requestId']}/r{value['revision']}"
    prefix = f"requests/{value['requestId']}/r{value['revision']}"
    report = (Path(packet) / 'report.md').read_text(encoding='utf-8')
    diagnostic = '\n\n'.join('### ' + key + '\n' + section['answer'] + '\nEvidence: ' + section['evidenceClass'] +
                              '; explanation: ' + section['explanationKind'] + '; references: ' + json.dumps(section['references'])
                              for key, section in value['diagnostics'].items())
    versions = {key: value['evidence'][key] for key in ('programKitVersion', 'profileVersion', 'knowledgeVersion', 'sourceCommit', 'dirtyState')}
    body = (tag + '\n' + f"Contract {c.VERSION}; project `{value['projectId']}`; component `{value['component']}`.\n\n" +
            report + '\n\nSelected versions/source: ' + json.dumps(versions) + '\n\n' + diagnostic +
            '\n\nOriginal account: ' + value['originalAccount'] + '\n\nUnclassified: ' + json.dumps(value['unclassified']) +
            '\n\nEvidence: ' + f'https://github.com/{account}/program-kit-evidence/tree/{branch}/{prefix}' +
            '\n\nOmissions: ' + json.dumps(value['omissions'], ensure_ascii=False))
    result = {'schemaVersion': 1, 'proof': proof, 'account': account, 'host': 'github.com', 'issueRepository': c.UPSTREAM,
              'evidenceRepository': c.EVIDENCE, 'fork': account + '/program-kit-evidence', 'baseBranch': 'main',
              'baseCommit': base_commit, 'validatorCommit': validator_commit, 'destination': destination,
              'rationale': rationale, 'correlation': correlation, 'branch': branch, 'prefix': prefix,
              'title': f"[{value['component']}] {value['title']}", 'body': body,
              'prBody': tag + f"\nproject `{value['projectId']}`\nEvidence for ISSUE_URL. Guardian and maintainer review required.\n" + rationale,
              'crossLinkBody': tag + '\nEvidence submission: PR_URL',
              'files': {n: {'sha256': c.sha(d), 'bytes': len(d)} for n, d in c.inventory(packet).items()},
              'publication': 'Issue/comment, consumer fork, evidence branch/push, PR, issue cross-link. Public Git history may persist indefinitely.'}
    result['reviewDigest'] = c.digest(result)
    c.require(len(body) <= 60000, 'portable-report-exceeds-issue-budget-select-shorter-summaries')
    c.sensitive(c.encoded(result))
    return result


def reconcile_issue(api, value, interrupted=False, known_number=None):
    tag = marker(value)
    if known_number is not None:
        issue = api.api('GET', f'repos/{c.UPSTREAM}/issues/{known_number}')
        c.require(tag in (issue.get('body') or ''), 'known-issue-request-marker-conflict')
        return issue
    # Bounded direct reconciliation avoids trusting a search index after response loss.
    found = []
    for page in (1, 2):
        batch = api.api('GET', f'repos/{c.UPSTREAM}/issues?state=all&sort=created&direction=desc&per_page=100&page={page}')
        for item in batch:
            if 'pull_request' not in item and tag in (item.get('body') or ''):
                found.append(api.api('GET', f"repos/{c.UPSTREAM}/issues/{item['number']}"))
        if len(batch) < 100 or found:
            break
    c.require(len(found) <= 1, 'ambiguous-existing-request-destination')
    c.require(found or not interrupted, 'interrupted-issue-create-unresolved-inspect-and-link-actual-issue-before-retry')
    return found[0] if found else None


def verify_deployment(api, base_commit, validator_commit):
    remote = api.api('GET', 'repos/' + c.EVIDENCE)
    c.require(remote['full_name'] == c.EVIDENCE and not remote['private'] and remote['default_branch'] == 'main', 'evidence-repository-unprovisioned-or-wrong-identity')
    main = api.api('GET', 'repos/' + c.EVIDENCE + '/commits/main')
    submission_base = main
    if main['sha'] != base_commit:
        comparison = api.api('GET', f'repos/{c.EVIDENCE}/compare/{base_commit}...{main["sha"]}')
        c.require(comparison.get('merge_base_commit', {}).get('sha') == base_commit and
                  comparison.get('status') in ('ahead', 'identical'), 'evidence-base-diverged-review-again')
        submission_base = api.api('GET', f'repos/{c.EVIDENCE}/commits/{base_commit}')
    deployment = api.api('GET', 'repos/' + c.EVIDENCE + '/contents/guardian-deployment.json?ref=' + main['sha'])
    config = json.loads(base64.b64decode(deployment['content']))
    c.require(config.get('validatorCommit') == validator_commit and config.get('contractVersion') == c.VERSION
              and type(config.get('repositoryRulesetId')) is int and config['repositoryRulesetId'] > 0
              and type(config.get('githubAppId')) is int and config['githubAppId'] > 0
              and config.get('githubAppSlug') == 'program-kit-evidence-guardian', 'trusted-guardian-not-configured')
    # Repository rules and App identity are public metadata. Consumers need no
    # organization Administration, upstream Write, or access to the App secret.
    app = api.api('GET', 'apps/' + config['githubAppSlug'])
    c.require(app.get('id') == config['githubAppId'] and app.get('owner', {}).get('login') == 'orbyss-io'
              and app.get('permissions') == {'checks': 'write', 'contents': 'read', 'pull_requests': 'read', 'metadata': 'read'},
              'dedicated-guardian-app-identity-or-permissions')
    rules = api.api('GET', f"repos/{c.EVIDENCE}/rulesets/{config['repositoryRulesetId']}?includes_parents=true")
    conditions = rules.get('conditions', {})
    branches = conditions.get('ref_name', {})
    c.require(rules.get('enforcement') == 'active' and rules.get('target') == 'branch' and not rules.get('bypass_actors')
              and rules.get('source_type') == 'Repository' and rules.get('source') == c.EVIDENCE
              and 'refs/heads/main' in branches.get('include', [])
              and not branches.get('exclude'), 'ruleset-must-enforce-main-and-repository-without-bypass')
    effective = []
    for page in range(1, 11):
        batch = api.api('GET', f'repos/{c.EVIDENCE}/rules/branches/main?per_page=100&page={page}')
        effective.extend(r for r in batch if r.get('ruleset_id') == config['repositoryRulesetId'])
        if len(batch) < 100:
            break
    else:
        raise ValueError('PKRF effective-rules-incomplete')
    # Evidence is append-only. Requiring a rebase after another request merges
    # would break immutable reviewed commits and response-loss retries. The
    # guardian checks ancestry; GitHub merge conflicts still block collisions.
    c.require(any(r.get('type') == 'required_status_checks' and
        r.get('parameters', {}).get('strict_required_status_checks_policy') is False and any(
        w.get('context') == 'program-kit-evidence/guardian' and w.get('integration_id') == config['githubAppId']
        for w in r.get('parameters', {}).get('required_status_checks', []))
        for r in effective) and any(r.get('type') == 'pull_request' and
        r.get('parameters', {}).get('required_approving_review_count', 0) >= 1 and
        all(r.get('parameters', {}).get(key) is True for key in ('dismiss_stale_reviews_on_push', 'require_code_owner_review', 'require_last_push_approval', 'required_review_thread_resolution'))
        for r in effective) and {'deletion', 'non_fast_forward'} <= {r.get('type') for r in effective},
        'app-bound-check-and-maintainer-review-rule-required')
    for name in ('.github/workflows/guardian.yml', '.github/CODEOWNERS', 'guardian.py', 'guardian_check.py', 'repair_contract.py'):
        trusted = api.api('GET', f'repos/{c.EVIDENCE}/contents/{name}?ref={validator_commit}')
        current = api.api('GET', f'repos/{c.EVIDENCE}/contents/{name}?ref={main["sha"]}')
        c.require(trusted.get('sha') and current.get('sha') == trusted['sha'], 'trusted-guardian-source-changed')
    return {'main': main, 'submissionBase': submission_base, 'repository': remote, 'retrievedAt': now(), 'rulesetId': config['repositoryRulesetId'],
            'validatorCommit': validator_commit, 'availability': 'configured',
            'githubAppId': config['githubAppId'], 'execution': 'maintainer-workflow-dispatch-from-main',
            'bypassVisibility': 'visible' if 'bypass_actors' in rules else 'not-disclosed-by-GitHub-to-read-only-consumer',
            'meaning': 'fresh configuration inspection; no submitted evidence or maintainer acceptance established'}


@contextmanager
def delivery_lock(root):
    directory, _ = personal(root)
    path = c.inside(directory, 'delivery.lock')
    # OS advisory lock is released even on process death; no stale sentinel or
    # second process can race the same consumer's issue creation/reconciliation.
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt': msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def public(root, packet, reviewed, approved_digest, api):
    with delivery_lock(root):
        return publish_locked(root, packet, reviewed, approved_digest, api)


def publish_locked(root, packet, reviewed, approved_digest, api):
    expected = dict(reviewed)
    digest = expected.pop('reviewDigest', None)
    c.require(digest == c.digest(expected) == approved_digest, 'exact-reviewed-content-approval-required')
    c.require(reviewed['issueRepository'] == c.UPSTREAM and reviewed['evidenceRepository'] == c.EVIDENCE and
              reviewed['host'] == 'github.com' and reviewed['baseBranch'] == 'main', 'public-destination-policy')
    proof = c.guard(packet)
    c.require(proof == reviewed['proof'] and {n: {'sha256': c.sha(d), 'bytes': len(d)} for n, d in c.inventory(packet).items()} == reviewed['files'], 'reviewed-packet-changed')
    value = read(Path(packet) / 'request.json')
    # Rebuild derived destinations/bodies so editing a review cannot redirect staging.
    rebuilt = plan(packet, reviewed['correlation'], reviewed['destination'], reviewed['rationale'],
                   reviewed['account'], reviewed['baseCommit'], reviewed['validatorCommit'])
    c.require(rebuilt == reviewed, 'review-plan-not-canonical')
    directory, _ = personal(root)
    journal = c.inside(directory, 'delivery/' + value['requestId'] + '/' + str(value['revision']) + '.json')
    history = read(journal, {'reviewDigest': digest, 'events': []})
    c.require(history['reviewDigest'] == digest, 'different-approved-revision-already-started')
    def event(kind, reference):
        row = {'kind': kind, 'reference': reference, 'recordedAt': now()}
        history['events'].append(row)
        write(journal, history)
    write(journal, history)
    c.require(api.auth() == reviewed['account'], 'github-account-changed')
    main = verify_deployment(api, reviewed['baseCommit'], reviewed['validatorCommit'])['submissionBase']
    known = {obj['number'] for record in read(directory / 'submissions.json', {'requests': []})['requests']
             if record.get('requestId') == value['requestId'] and record.get('revision') == value['revision']
             and record.get('requestSha256') == proof['requestSha256']
             for obj in record.get('objects', []) if obj['repository'] == c.UPSTREAM and obj['kind'] == 'issue'}
    for entry in history['events']:
        match = re.fullmatch(r'https://github.com/' + re.escape(c.UPSTREAM) + r'/issues/([1-9][0-9]*)', entry['reference'])
        if entry['kind'] == 'issue' and match: known.add(int(match[1]))
    c.require(len(known) <= 1, 'ambiguous-known-issue-references')
    issue = reconcile_issue(api, value, any(e['kind'] == 'attempt-create-issue' for e in history['events']),
                            next(iter(known), None)) if reviewed['destination'] == 'new' else api.api('GET', f"repos/{c.UPSTREAM}/issues/{reviewed['destination']}")
    if issue is None:
        event('attempt-create-issue', marker(value))
        issue = api.api('POST', f'repos/{c.UPSTREAM}/issues', {'title': reviewed['title'], 'body': reviewed['body']})
    elif reviewed['destination'] != 'new':
        comments = pages(api, f"repos/{c.UPSTREAM}/issues/{issue['number']}/comments")
        if not any(comment.get('body') == reviewed['body'] for comment in comments):
            c.require(not any(marker(value) in (comment.get('body') or '') and 'Evidence submission:' not in comment.get('body', '') for comment in comments), 'remote-comment-content-conflict')
            event('attempt-comment', issue['html_url'])
            comment = api.api('POST', f"repos/{c.UPSTREAM}/issues/{issue['number']}/comments", {'body': reviewed['body']})
            event('comment', comment['html_url'])
    else:
        c.require(issue['body'] == reviewed['body'], 'remote-issue-content-conflict')
    event('issue', issue['html_url'])
    # Enumerate actual forks; reuse only the selected account's correctly parented fork.
    forks = pages(api, f"repos/{c.EVIDENCE}/forks")
    fork = next((f for f in forks if f['full_name'] == reviewed['fork']), None)
    if fork is None:
        event('attempt-fork', reviewed['fork'])
        fork = api.api('POST', f'repos/{c.EVIDENCE}/forks', {'default_branch_only': True})
    actual = api.api('GET', 'repos/' + reviewed['fork'])
    c.require(actual['full_name'] == reviewed['fork'] and actual.get('parent', {}).get('full_name') == c.EVIDENCE, 'fork-not-ready-or-wrong-parent-retry-after-inspection')
    event('fork', actual['html_url'])
    # Git Data API builds one commit from the reviewed inventory. No consumer code,
    # Git hooks, arbitrary git config or upstream Write permission participates.
    base_tree = main['commit']['tree']['sha']
    tree = []
    for name, data in c.inventory(packet).items():
        blob = api.api('POST', 'repos/' + reviewed['fork'] + '/git/blobs', {'content': base64.b64encode(data).decode(), 'encoding': 'base64'})
        tree.append({'path': reviewed['prefix'] + '/' + name, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    built = api.api('POST', 'repos/' + reviewed['fork'] + '/git/trees', {'base_tree': base_tree, 'tree': tree})
    refs = pages(api, 'repos/' + reviewed['fork'] + '/git/matching-refs/heads/repair/')
    ref = next((r for r in refs if r['ref'] == 'refs/heads/' + reviewed['branch']), None)
    if ref:
        commit = api.api('GET', 'repos/' + reviewed['fork'] + '/git/commits/' + ref['object']['sha'])
        c.require(commit['tree']['sha'] == built['sha'] and [p['sha'] for p in commit['parents']] == [main['sha']], 'submission-branch-content-conflict')
    else:
        commit = api.api('POST', 'repos/' + reviewed['fork'] + '/git/commits', {'message': marker(value), 'tree': built['sha'], 'parents': [main['sha']]})
        event('attempt-branch', reviewed['branch'])
        api.api('POST', 'repos/' + reviewed['fork'] + '/git/refs', {'ref': 'refs/heads/' + reviewed['branch'], 'sha': commit['sha']})
    event('branch', commit['sha'])
    prs = pages(api, f"repos/{c.EVIDENCE}/pulls?state=all&head=" + quote(reviewed['account'] + ':' + reviewed['branch'], safe=''))
    c.require(len(prs) <= 1, 'ambiguous-evidence-pr')
    body = reviewed['prBody'].replace('ISSUE_URL', issue['html_url'])
    if prs:
        pr = prs[0]
        c.require(pr['body'] == body and pr['head']['sha'] == commit['sha'] and pr['base']['ref'] == 'main', 'existing-pr-content-conflict')
    else:
        event('attempt-pr', reviewed['branch'])
        pr = api.api('POST', f'repos/{c.EVIDENCE}/pulls', {'title': reviewed['title'], 'body': body,
                    'head': reviewed['account'] + ':' + reviewed['branch'], 'base': 'main'})
    event('evidence-pr', pr['html_url'])
    link = reviewed['crossLinkBody'].replace('PR_URL', pr['html_url'])
    comments = pages(api, f"repos/{c.UPSTREAM}/issues/{issue['number']}/comments")
    if not any(comment.get('body') == link for comment in comments):
        event('attempt-cross-link', issue['html_url'])
        api.api('POST', f"repos/{c.UPSTREAM}/issues/{issue['number']}/comments", {'body': link})
    receipt = {'deliveredAt': now(), 'reviewDigest': digest, 'issue': issue['html_url'], 'evidencePR': pr['html_url'], 'commit': commit['sha']}
    remember(root, {'requestId': value['requestId'], 'projectId': value['projectId'], 'revision': value['revision'],
                    'requestSha256': proof['requestSha256'], 'route': 'public', 'account': reviewed['account'], 'host': 'github.com',
                    'objects': [{'repository': c.UPSTREAM, 'kind': 'issue', 'number': issue['number']},
                                {'repository': c.EVIDENCE, 'kind': 'evidence-pr', 'number': pr['number']}], 'receipt': receipt})
    return receipt


def status(records, api=None):
    result = {'retrievedAt': now(), 'sources': [], 'lifecycle': {key: 'unknown' for key in c.LIFECYCLE},
              'meaning': 'fresh per-source observations, not an atomic snapshot; no lifecycle inference from issue state'}
    for record in records:
        if record['route'] == 'local':
            try:
                ledger = read(record['ledger'])
                c.require(ledger is not None, 'local-ledger-unavailable')
                result['sources'].append({'source': 'local', 'ledger': record['ledger'], 'availability': 'available', 'data': ledger, 'retrievedAt': now()})
            except (OSError, ValueError):
                result['sources'].append({'source': 'local', 'availability': 'unavailable', 'retrievedAt': now()})
        for obj in record.get('objects', []):
            repository, number, kind = obj['repository'], obj['number'], obj['kind']
            c.require(repository in (c.UPSTREAM, c.EVIDENCE) and type(number) is int and number > 0 and
                      kind in ('issue', 'evidence-pr', 'implementation-pr', 'release'), 'known-object-reference')
            source = {'source': 'github', 'reference': obj, 'retrievedAt': now()}
            try:
                c.require(api is not None, 'github-status-unavailable')
                if kind == 'release':
                    source['data'] = api.api('GET', f'repos/{repository}/releases/{number}')
                else:
                    endpoint = f'repos/{repository}/' + ('issues/' if kind == 'issue' else 'pulls/') + str(number)
                    data = api.api('GET', endpoint)
                    source['data'] = data
                    source['comments'] = pages(api, f'repos/{repository}/issues/{number}/comments')
                    if kind != 'issue':
                        source['reviews'] = pages(api, endpoint + '/reviews')
                        source['reviewComments'] = pages(api, endpoint + '/comments')
                        checks = api.api('GET', f"repos/{repository}/commits/{data['head']['sha']}/check-runs?per_page=100&page=1")
                        runs = list(checks['check_runs'])
                        for page in range(2, (checks['total_count'] + 99) // 100 + 1):
                            runs.extend(api.api('GET', f"repos/{repository}/commits/{data['head']['sha']}/check-runs?per_page=100&page={page}")['check_runs'])
                        source['checks'] = runs
                        source['commitStatuses'] = pages(api, f"repos/{repository}/commits/{data['head']['sha']}/statuses")
                source['availability'] = 'available'
            except (OSError, ValueError, KeyError):
                source['availability'] = 'partial' if 'data' in source else 'unavailable'
            result['sources'].append(source)
    return result


def discover(api, account, project_id=None):
    c.require(re.fullmatch(r'[A-Za-z0-9-]+', account), 'account')
    records, queries = {}, []
    for repository in (c.UPSTREAM, c.EVIDENCE):
        for qualifier in ('author', 'commenter', 'involves'):
            query = f'repo:{repository} {qualifier}:{account} "program-kit-repair"'
            queries.append(query)
            page = 1
            while True:
                result = api.api('GET', 'search/issues?q=' + quote(query, safe='') + f'&per_page=100&page={page}')
                c.require(not result.get('incomplete_results') and result['total_count'] <= 1000, 'history-search-incomplete-refine-scope')
                for item in result['items']:
                    # Search discovers references; direct objects/comments establish provenance.
                    obj = api.api('GET', f"repos/{repository}/issues/{item['number']}")
                    comments = pages(api, f"repos/{repository}/issues/{item['number']}/comments")
                    bodies = [obj.get('body') or '', *[x.get('body') or '' for x in comments]]
                    if project_id is None or any(f'project `{project_id}`' in body for body in bodies):
                        records[(repository, item['number'])] = {'repository': repository, 'number': item['number'],
                            'kind': ('evidence-pr' if repository == c.EVIDENCE else 'implementation-pr') if 'pull_request' in obj else 'issue'}
                if page * 100 >= result['total_count']:
                    break
                page += 1
    return {'retrievedAt': now(), 'scope': 'project' if project_id else 'account', 'projectId': project_id,
            'queries': queries, 'objects': list(records.values()), 'meaning': 'discovered references; status requires fresh direct reads'}


def recover(root, api, project_id, known_objects=None):
    """Reconstruct reference-only index entries using fresh bodies/comments/markers."""
    c.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}', project_id), 'stable-public-project-pseudonym')
    account = api.auth()
    objects = known_objects if known_objects is not None else discover(api, account, project_id)['objects']
    recovered = []
    for obj in objects:
        c.fields(obj, ('repository', 'number', 'kind'))
        c.require(obj['repository'] in (c.UPSTREAM, c.EVIDENCE) and type(obj['number']) is int and obj['number'] > 0 and
                  obj['kind'] in ('issue', 'evidence-pr', 'implementation-pr', 'release'), 'known-object-reference')
        if obj['kind'] == 'release': continue  # Release linking is explicit, not inferred from prose.
        endpoint = f"repos/{obj['repository']}/issues/{obj['number']}"
        data = api.api('GET', endpoint)
        comments = pages(api, endpoint + '/comments')
        bodies = [data.get('body') or '', *[x.get('body') or '' for x in comments]]
        for body in bodies:
            if f'project `{project_id}`' not in body: continue
            for request_id, revision, sha in re.findall(r'<!-- program-kit-repair (' + c.ID + r') revision=([1-9][0-9]*) sha256=(' + c.HEX + r') -->', body):
                reference = {'requestId': request_id, 'projectId': project_id, 'revision': int(revision), 'requestSha256': sha,
                             'route': 'public', 'account': account, 'host': 'github.com', 'objects': [obj]}
                remember(root, reference)
                if reference not in recovered: recovered.append(reference)
    return {'retrievedAt': now(), 'scope': 'project', 'references': recovered,
            'meaning': 'recovered object/marker references, not authenticated publisher identity or current status'}


def link(root, request_id, objects):
    """Record explicitly selected implementation PR/release references; never state."""
    directory, _ = personal(root)
    records = read(directory / 'submissions.json')['requests']
    original = next((r for r in reversed(records) if r['requestId'] == request_id), None)
    c.require(original is not None, 'unknown-request-recover-first')
    record = {key: value for key, value in original.items() if key != 'receipt'}
    record['objects'] = objects
    remember(root, record)
    return {'linkedReferences': objects, 'meaning': 'references only; status is always freshly retrieved'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('configure'); p.add_argument('--mode', choices=('consumer', 'contributor'), required=True); p.add_argument('--checkout', type=Path)
    sub.add_parser('clear-preferences')
    sub.add_parser('prerequisites')
    p = sub.add_parser('draft'); p.add_argument('--project', required=True); p.add_argument('--title', required=True); p.add_argument('--previous', type=Path); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('prepare'); p.add_argument('--source', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('validate'); p.add_argument('--packet', type=Path, required=True)
    p = sub.add_parser('local'); p.add_argument('--packet', type=Path, required=True); p.add_argument('--ledger', required=True); p.add_argument('--correlation', type=Path)
    p = sub.add_parser('search'); p.add_argument('--terms', required=True); p.add_argument('--alternate', required=True); p.add_argument('--refine'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('plan'); p.add_argument('--packet', type=Path, required=True); p.add_argument('--correlation', type=Path, required=True); p.add_argument('--destination', required=True); p.add_argument('--rationale', required=True); p.add_argument('--account', required=True); p.add_argument('--base-commit', required=True); p.add_argument('--validator-commit', required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('publish'); p.add_argument('--packet', type=Path, required=True); p.add_argument('--review', type=Path, required=True); p.add_argument('--approved-digest', required=True)
    p = sub.add_parser('history'); p.add_argument('--project'); p.add_argument('--account-wide', action='store_true')
    p = sub.add_parser('status'); p.add_argument('--request-id', required=True)
    p = sub.add_parser('recover'); p.add_argument('--project', required=True); p.add_argument('--known-objects', type=Path)
    p = sub.add_parser('link'); p.add_argument('--request-id', required=True); p.add_argument('--objects', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'configure': result = configure(args.root, args.mode, args.checkout)
        elif args.command == 'clear-preferences':
            directory, _ = personal(args.root); (directory / 'preferences.json').unlink(); result = {'cleared': 'routing choices; historical submission references retained'}
        elif args.command == 'prerequisites':
            api = GitHub(); result = {'executable': api.executable, 'host': api.host, 'account': api.auth()}
        elif args.command == 'draft':
            result = draft(args.project, args.title, previous=read(args.previous) if args.previous else None,
                           previous_sha=c.sha(args.previous.read_bytes()) if args.previous else None); write(args.output, result, immutable=True)
        elif args.command == 'prepare': result = prepare(args.source, args.output)
        elif args.command == 'validate': result = c.guard(args.packet)
        elif args.command == 'local': result = local(args.root, args.packet, args.ledger, read(args.correlation) if args.correlation else None)
        elif args.command == 'search':
            api = GitHub(); api.auth(); result = search(api, args.terms, args.alternate, args.refine); write(args.output, result)
        elif args.command == 'plan':
            destination = int(args.destination) if args.destination.isdigit() else args.destination
            result = plan(args.packet, read(args.correlation), destination, args.rationale, args.account, args.base_commit, args.validator_commit); write(args.output, result)
        elif args.command == 'publish': result = public(args.root, args.packet, read(args.review), args.approved_digest, GitHub())
        elif args.command == 'history':
            directory, _ = personal(args.root)
            if args.account_wide:
                api = GitHub(); result = discover(api, api.auth())
            else:
                c.require(args.project, 'history-default-requires-project-id')
                refs = [r for r in read(directory / 'submissions.json')['requests'] if r['projectId'] == args.project]
                result = {'scope': 'project', 'references': refs}
                try:
                    api = GitHub(); result['discovery'] = discover(api, api.auth(), args.project)
                except (ValueError, OSError): result['discovery'] = {'availability': 'unavailable'}
        elif args.command == 'status':
            directory, _ = personal(args.root)
            refs = [r for r in read(directory / 'submissions.json')['requests'] if r['requestId'] == args.request_id]
            c.require(refs, 'unknown-request-discover-history-first')
            try: api = GitHub(); api.auth()
            except (ValueError, OSError): api = None
            result = status(refs, api)
        elif args.command == 'recover': result = recover(args.root, GitHub(), args.project, read(args.known_objects) if args.known_objects else None)
        elif args.command == 'link': result = link(args.root, args.request_id, read(args.objects))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, json.JSONDecodeError, subprocess.SubprocessError):
        # Do not echo submitted data or raw platform errors; prepared records survive.
        error = sys.exc_info()[1]
        print(str(error) if isinstance(error, ValueError) and str(error).startswith('PKRF ') else
              'PKRF operation-unavailable-local-report-preserved-inspect-historical-delivery-journal-before-retry', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
